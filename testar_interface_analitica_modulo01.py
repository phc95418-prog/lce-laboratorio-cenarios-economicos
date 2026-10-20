"""Integração real do script Streamlit via AppTest; visual depende do navegador."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest
from analise_modulo01 import DIMENSOES, analisar_exploracao, analisar_experimento_a, analisar_experimento_b
from experimentos import cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios
from modelo_mercado import simular_mercado
from interface_analise_modulo01 import _equacao


def aba(at, nome):
    return next(t for t in at.tabs if t.label == nome)


def textos(elemento):
    return "\n".join(e.value.replace(r"\$", "$") for e in elemento.markdown)


class InterfaceAnalitica(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=15).run()
        self.assertFalse(self.at.exception)

    def ambiente(self, nome):
        self.at.radio(key="lce_ambiente").set_value(nome).run()
        self.assertFalse(self.at.exception)

    def test_livre_tres_dimensoes_sintese_visivel_e_recolhido(self):
        sim = aba(self.at, "Simulação")
        self.assertEqual([t.label for t in sim.expander[0].tabs], list(DIMENSOES))
        self.assertFalse(sim.expander[0].proto.expanded)
        self.assertEqual(sim.expander[0].key, "lce_analise_individual")
        esperado = analisar_exploracao(simular_mercado(100,1,20,1,20))
        self.assertIn(esperado.sintese, textos(sim))
        self.assertNotIn(esperado.sintese, textos(sim.expander[0]))
        self.assertIn(esperado.base, "\n".join(c.value for c in sim.caption))
        self.assertEqual(len(aba(self.at,"Comparar cenários").info), 1)
        self.assertEqual(len(aba(self.at,"Comparar cenários").expander), 0)

    def test_a_destaque_individual_comparacao_completa(self):
        self.ambiente("Experimento A")
        self.at.selectbox(key="lce_cenario_destaque_a").set_value("B · Demanda menos elástica").run()
        sim, comp = aba(self.at,"Simulação"), aba(self.at,"Comparar cenários")
        cenarios = resultados_cenarios(cenarios_experimento_a(20))
        individual = analisar_exploracao(cenarios[1][1], nome=cenarios[1][0])
        comparativa = analisar_experimento_a(cenarios)
        self.assertIn(individual.sintese,textos(sim))
        self.assertNotIn(cenarios[0][0],textos(sim))
        self.assertIn(comparativa.sintese,textos(comp))
        for nome,_ in cenarios:
            self.assertIn(nome,textos(comp))
        self.assertEqual([t.label for t in comp.expander[0].tabs],list(DIMENSOES))
        self.assertFalse(comp.expander[0].proto.expanded)

    def test_b_individual_comparacao_completa_e_fronteira_mista(self):
        self.ambiente("Experimento B")
        self.at.slider(key="lce_imposto_comum_b").set_value(40).run()
        sim, comp = aba(self.at,"Simulação"),aba(self.at,"Comparar cenários")
        self.assertIn("sem preços transacionados",textos(sim))
        cenarios = resultados_cenarios(cenarios_experimento_b(40))
        self.assertIn(analisar_experimento_b(cenarios).sintese,textos(comp))
        for nome,_ in cenarios:
            self.assertIn(nome,textos(comp))
        self.assertEqual([t.label for t in comp.expander[0].tabs],list(DIMENSOES))
        self.assertEqual(self.at.metric[3].value,"—")
        self.assertIn("B2",textos(comp))
        self.assertTrue(comp.warning)

    def test_regimes_livre_e_a_zero_interior_proibitivo(self):
        for imposto in (0,20,90):
            with self.subTest(livre=imposto):
                self.at.number_input(key="lce_imposto_livre").set_value(imposto).run()
                self.assertFalse(self.at.exception)
                analise = analisar_exploracao(simular_mercado(100,1,20,1,imposto))
                self.assertIn(analise.sintese,textos(aba(self.at,"Simulação")))
        self.ambiente("Experimento A")
        for imposto in (0,20,80):
            with self.subTest(a=imposto):
                self.at.slider(key="lce_imposto_comum_a").set_value(imposto).run()
                self.assertFalse(self.at.exception)
                self.assertIn(analisar_experimento_a(resultados_cenarios(cenarios_experimento_a(imposto))).sintese,
                              textos(aba(self.at,"Comparar cenários")))

    def test_abertura_paineis_nao_modifica_parametros_ou_resultados(self):
        self.ambiente("Experimento A")
        antes = [m.value for m in self.at.metric]
        controles = (self.at.slider[0].value,self.at.selectbox[0].value)
        for aberto in (True,False,True):
            for key in ("lce_analise_individual","lce_analise_comparativa_a"):
                self.at.session_state[key] = aberto
            self.at.run()
            self.assertFalse(self.at.exception)
            self.assertEqual([m.value for m in self.at.metric],antes)
            self.assertEqual((self.at.slider[0].value,self.at.selectbox[0].value),controles)
            self.assertEqual([e.proto.expanded for e in self.at.expander if e.key and e.key.startswith("lce_analise_")], [aberto,aberto])

    def test_identidade_painel_estavel_durante_fronteiras_de_a(self):
        # AppTest não oferece evento de abertura/fechamento do expander.
        # Sua serialização não comprova persistência visual: verificar no browser.
        self.ambiente("Experimento A")
        inicial = aba(self.at,"Comparar cenários").expander[0].proto.id
        for t in (0,1,60,80,20):
            self.at.slider[0].set_value(t).run()
            self.assertFalse(self.at.exception)
            self.assertEqual(aba(self.at,"Comparar cenários").expander[0].proto.id,inicial)

    def test_controles_graficos_tabela_e_modelo_preservados(self):
        self.assertEqual(len(self.at.metric),10)
        self.assertEqual(len(self.at.get("plotly_chart")),2)
        self.assertEqual(len(self.at.number_input),5)
        self.at.radio(key="lce_forma_entrada").set_value("Avançado · equações").run()
        self.assertEqual(len(self.at.number_input),5)
        self.assertEqual(self.at.metric[1].value,"30,00")
        for ambiente, limite in (("Experimento A",80),("Experimento B",40)):
            self.ambiente(ambiente)
            self.assertEqual(self.at.slider[0].max,limite)
            self.assertEqual(len(self.at.selectbox[0].options),3)
            self.assertEqual(len(self.at.get("plotly_chart")),3)
            self.assertEqual(len(self.at.dataframe[0].value),3)
            # Etapa 3A: método migrou para a engrenagem, sem nova aba.
            self.assertNotIn("Modelo e hipóteses", [t.label for t in self.at.tabs])
            self.assertTrue(next(e for e in self.at.expander if e.label=="Curvas, equilíbrio e incidência").latex)

    def test_sem_perguntas_niveis_ou_explicacoes_redundantes(self):
        for ambiente in ("Exploração livre","Experimento A","Experimento B"):
            self.ambiente(ambiente)
            tudo = textos(self.at)
            for proibido in ("Experimente observar","questão sugerida","O que aconteceu neste mercado?","O que observar:"):
                self.assertNotIn(proibido,tudo)
            self.assertFalse(any(r.label in ("O que você quer investigar?","Nível de aprofundamento") for r in self.at.radio))
            self.assertFalse(any(e.label.startswith(("💡 Questões","📖 Compreenda","Síntese econômica · após","Por que isso acontece?")) for e in self.at.expander))

    def test_latex_e_valores_monetarios_recebidos_sem_recalculo(self):
        formulas = aba(self.at,"Simulação").latex
        self.assertTrue(any(r"P_C=100-(1)(30)\approx 70" in f.value for f in formulas))
        self.assertFalse(any(r",\quad" in f.value for f in formulas))
        self.assertTrue(any(r"R\$ 600,00" in m.value for m in aba(self.at,"Simulação").markdown))
        self.assertEqual(_equacao(r"x=1,\quad y=2"),r"\begin{aligned}&x=1\\&y=2\end{aligned}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
