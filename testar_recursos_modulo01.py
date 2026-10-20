"""Contratos de Ajuda, documentação migrada e isolamento de recursos do M01."""
import ast
import json
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest
from recursos_modulo01 import perguntas_frequentes, SOBRE_MODELO, MIGRACAO


class Recursos(unittest.TestCase):
    def iniciar(self):
        at=AppTest.from_file(str(Path(__file__).with_name("app.py")),default_timeout=15).run()
        self.assertFalse(at.exception)
        return at

    def test_ajuda_contextual_nos_tres_ambientes_sem_atividades(self):
        for ambiente in ("Exploração livre","Experimento A","Experimento B"):
            faq=perguntas_frequentes(ambiente)
            self.assertEqual(len(faq),7)
            texto=" ".join(r for _,r in faq)
            for termo in ("Simulação","Comparar cenários","engrenagem","Análise econômica e matemática"):
                self.assertIn(termo,texto)
            for termo in ("experimente","exercício","desafio","aumente","reduza","pontuação"):
                self.assertNotIn(termo,texto.lower())

    def test_migracao_completa_equacoes_e_referencias(self):
        self.assertEqual(len(MIGRACAO),8)
        formulas=" ".join(f for _,_,fs in SOBRE_MODELO for f in fs)
        for trecho in (r"P_D(Q)=a-bQ",r"P_S(Q)=c+dQ",r"Q_0=\frac{a-c}{b+d}",
                       r"Q_t=\max",r"P_C-P_P=t",r"\int_0^Q",r"(Q_0-Q_t)^2"):
            self.assertIn(trecho,formulas)
        textos=" ".join(t for _,ts,_ in SOBRE_MODELO for t in ts)
        for trecho in ("Varian & Melitz","OpenStax","Benzarti","2025","custos de arrecadação",
                       "efeitos-renda","distribuição","uso da receita pública","inferior a 1",
                       "não equivale automaticamente ao lucro", "não preços negociados"):
            self.assertIn(trecho,textos)

    def test_documentacao_sem_preco_negociado_na_fronteira(self):
        textos=" ".join(t for _,ts,_ in SOBRE_MODELO for t in ts)
        for trecho in ("Imposto zero", "preços válidos", "Em t≥a−c", "não se aplicam",
                       "não se extrapolam identidades interiores", "coeficientes potenciais"):
            self.assertIn(trecho,textos)

    def test_duas_abas_e_acessos_permanentes(self):
        at=self.iniciar()
        self.assertEqual([t.label for t in at.tabs if t.label not in ("Leitura econômica","Estrutura matemática","Propriedades e limites")],
                         ["Simulação","Comparar cenários"])
        self.assertEqual(len(at.get("popover")),2)
        self.assertTrue(any(e.label=="Sobre o modelo" for e in at.expander))
        for titulo,_,_ in SOBRE_MODELO:
            self.assertTrue(any(e.label==titulo for e in at.expander),titulo)

    def test_documentacao_ajuda_e_rerun_preservam_resultados(self):
        at=self.iniciar()
        for ambiente in ("Exploração livre","Experimento A","Experimento B"):
            at.radio(key="lce_ambiente").set_value(ambiente).run()
            valores=[m.value for m in at.metric]
            antes=at.number_input[0].value if ambiente=="Exploração livre" else at.slider[0].value
            for aberto in (True,False):
                at.session_state["lce_m01_sobre_modelo"]=aberto
                at.run()
                self.assertFalse(at.exception)
                self.assertEqual([m.value for m in at.metric],valores)
                depois=at.number_input[0].value if ambiente=="Exploração livre" else at.slider[0].value
                self.assertEqual(antes,depois)
            # Abertura do popover e mudança de tema são verificadas no browser.

    def test_consulta_parametros_somente_leitura_sem_novos_controles(self):
        at=self.iniciar()
        self.assertEqual(len(at.number_input),5)
        self.assertEqual(len(at.radio),2)
        consulta=next(e for e in at.expander if e.label.startswith("Parâmetros do mercado selecionado"))
        parametros=json.loads(consulta.json[0].value)
        self.assertEqual(parametros,{"a":100,"b":1,"c":20,"d":1,"t":20})
        self.assertFalse(consulta.number_input or consulta.slider or consulta.radio)

    def test_componente_pode_registrar_em_sessoes_independentes(self):
        a=self.iniciar();b=self.iniciar()
        self.assertEqual([m.value for m in a.metric],[m.value for m in b.metric])
        self.assertFalse(b.exception)

    def test_recursos_nao_dependem_de_m02_ou_exportacoes(self):
        raiz=Path(__file__).parent
        for nome in ("recursos_modulo01.py","interface_recursos_modulo01.py"):
            codigo=(raiz/nome).read_text(encoding="utf-8")
            arvore=ast.parse(codigo)
            modulos=[n.module or "" for n in ast.walk(arvore) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(any(m.startswith("modulo_02") for m in modulos))
            self.assertNotIn("download_button(",codigo)
            self.assertNotIn("m02_",codigo)

    def test_estilos_da_aplicacao_delimitados_ao_m01(self):
        codigo=Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        css=codigo.split("<style>",1)[1].split("</style>",1)[0]
        self.assertNotIn('\n      div[data-testid=',css)
        self.assertIn('body:has(.st-key-lce_m01_root)',css)
        self.assertIn('var(--text-color)',css)
        self.assertNotIn('st.set_option(',codigo)


if __name__=="__main__":
    unittest.main(verbosity=2)
