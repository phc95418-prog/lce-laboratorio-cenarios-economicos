"""Testes de regressão da investigação opcional do Experimento A."""

import unittest

from experimentos import cenarios_experimento_a, resultados_cenarios
from investigacao_a import QUESTOES, NIVEIS, sugestao, explicacao, formula, sintese


class TestesInvestigacaoA(unittest.TestCase):
    def setUp(self):
        self.cenarios = {
            t: resultados_cenarios(cenarios_experimento_a(t))
            for t in (0, 20, 40, 80)
        }

    def test_tres_questoes_sem_exigencia_de_resposta(self):
        self.assertEqual(set(QUESTOES), {"incidencia", "quantidade", "imposto"})

    def test_tres_niveis_progressivos(self):
        self.assertEqual(NIVEIS, ("Intuição", "Leitura dos gráficos", "Matemática"))

    def test_todos_estados_questoes_niveis_tem_conteudo(self):
        for t, cenarios in self.cenarios.items():
            for q in QUESTOES:
                with self.subTest(t=t, pergunta=q):
                    self.assertGreater(len(sugestao(q, cenarios)), 45)
                for nivel in NIVEIS:
                    with self.subTest(t=t, pergunta=q, nivel=nivel):
                        self.assertGreater(len(explicacao(q, nivel, cenarios)), 65)
                        self.assertEqual(formula(q, nivel) is not None, nivel == "Matemática")

    def test_sem_imposto_nao_afirma_incidente_efetivo(self):
        cenarios = self.cenarios[0]
        self.assertIn("não há carga tributária efetiva", sugestao("incidencia", cenarios))
        self.assertIn("Sem imposto", explicacao("incidencia", "Intuição", cenarios))
        self.assertIn("*potenciais*", explicacao("incidencia", "Leitura dos gráficos", cenarios))

    def test_sem_transacoes_nao_afirma_incidente_efetivo(self):
        cenarios = self.cenarios[80]
        for nivel in NIVEIS:
            texto = explicacao("incidencia", nivel, cenarios)
            self.assertIn("potencia", texto.lower())
        self.assertIn("Sem trocas", explicacao("incidencia", "Intuição", cenarios))
        self.assertIn("Sem transações", sugestao("imposto", cenarios))

    def test_parametros_a_consistentes_com_matematica_ensinada(self):
        for t, cenarios in self.cenarios.items():
            for nome, r in cenarios:
                with self.subTest(t=t, nome=nome):
                    self.assertAlmostEqual(r["q0"], 40)
                    self.assertAlmostEqual(r["b"] + r["d"], 2)
                    self.assertAlmostEqual(r["qt"], max(0, 40 - t/2))
                    self.assertAlmostEqual(r["arrecadacao"], t*r["qt"])
                    self.assertAlmostEqual(r["peso_morto"], (2/2)*(40-r["qt"])**2)

    def test_arrecadacao_maxima_a_em_40(self):
        arrecadacoes = [resultados_cenarios(cenarios_experimento_a(t))[0][1]["arrecadacao"]
                        for t in range(81)]
        self.assertEqual(arrecadacoes.index(max(arrecadacoes)), 40)
        self.assertEqual(arrecadacoes[80], 0)

    def test_leitura_grafica_incidencia_responde_ao_imposto_atual(self):
        cenarios = resultados_cenarios(cenarios_experimento_a(30))
        leitura = explicacao("incidencia", "Leitura dos gráficos", cenarios)
        self.assertIn("R$ 30,00", leitura)
        self.assertIn("R$ 15,00", leitura)  # simétrico: metade para cada lado
        self.assertIn("R$ 22,50", leitura)  # demanda menos elástica: 75% ao consumidor
        self.assertIn("R$ 7,50", leitura)   # oferta menos elástica: 25% ao consumidor
        self.assertIn("B · Demanda menos elástica", leitura)

    def test_matematica_incidencia_conecta_parametros_reais(self):
        cenarios = self.cenarios[20]
        texto = explicacao("incidencia", "Matemática", cenarios)
        self.assertIn("75%", texto)
        self.assertIn("25%", texto)
        self.assertIn("R$ 15,00", texto)
        self.assertIn("R$ 5,00", texto)

    def test_imposto_zero_quantidade_nao_afirma_qt_zero(self):
        sugestao_zero = sugestao("quantidade", self.cenarios[0])
        self.assertIn("coincide com Q₀", sugestao_zero)
        self.assertNotIn("Q após imposto, que agora é zero", sugestao_zero)
        conclusao = sintese("quantidade", self.cenarios[0])
        self.assertIn("potenciais", conclusao)
        self.assertNotIn("parcelas **efetivas**", conclusao)

    def test_sintese_contextual_e_sem_incidencia_efetiva_ficticia(self):
        for t in (0, 20, 40, 80):
            for questao in QUESTOES:
                resultado = sintese(questao, self.cenarios[t])
                self.assertGreater(len(resultado), 90)
                self.assertIn("R$", resultado) if questao != "incidencia" else None
        for t in (0, 80):
            self.assertIn("potenciais", sintese("incidencia", self.cenarios[t]))
            self.assertIn("potenciais", sintese("quantidade", self.cenarios[t]))

    def test_sintese_incidencia_distingue_percentual_de_valor_unitario(self):
        texto = sintese("incidencia", self.cenarios[20])
        self.assertIn("parcela percentual do imposto", texto)
        self.assertNotIn("carga unitária", texto.lower())
        self.assertIn("50%, 75%, 25%", texto)

    def test_sintese_imposto_60_relaciona_receita_e_peso_morto(self):
        cenarios = resultados_cenarios(cenarios_experimento_a(60))
        texto = sintese("imposto", cenarios)
        for trecho in ("R$ 60,00", "10,00", "R$ 600,00", "R$ 900,00",
                       "R$ 800,00", "R$ 40,00", "R$ 80,00"):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, texto)
        self.assertIn("arrecadação diminui", texto)

    def test_sintese_imposto_condicoes_extremas(self):
        zero = sintese("imposto", self.cenarios[0])
        proibitivo = sintese("imposto", self.cenarios[80])
        self.assertIn("R$ 0,00", zero)
        self.assertIn("R$ 0,00", proibitivo)
        self.assertIn("R$ 1.600,00", proibitivo)
        self.assertIn("não há transações", proibitivo)

    def test_regressao_introducao_nao_antecipa_resultado(self):
        from pathlib import Path
        codigo = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        trecho = codigo.split('if experiencia == "Experimento A":', 2)[-1]
        trecho = trecho.split('# Roteiro opcional:', 1)[0]
        self.assertNotIn('**O que observar:** a parcela', trecho)
        self.assertIn('"Três mercados partem do **mesmo equilíbrio inicial**', trecho)

    def test_leitura_grafica_separa_imposto_zero_de_sem_transacoes(self):
        sem_imposto = explicacao("incidencia", "Leitura dos gráficos", self.cenarios[0])
        sem_transacoes = explicacao("incidencia", "Leitura dos gráficos", self.cenarios[80])
        self.assertIn("continuam realizando transações", sem_imposto)
        self.assertIn("P₀ = R$ 60,00", sem_imposto)
        self.assertIn("preços pagos e recebidos são válidos", sem_imposto)
        self.assertIn("*potenciais*", sem_imposto)
        self.assertIn("nenhuma unidade é comercializada", sem_transacoes)
        self.assertIn("Não existem preços efetivos", sem_transacoes)
        self.assertNotIn("preços pagos e recebidos são válidos", sem_transacoes)

    def test_tres_expanders_investigacao_preservam_estado(self):
        """Protege as opções da API Streamlit; interação visual requer navegador."""
        import ast
        from pathlib import Path

        arvore = ast.parse(Path(__file__).with_name("app.py").read_text(encoding="utf-8"))
        encontrados = {}
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call):
                continue
            if not (isinstance(no.func, ast.Attribute) and no.func.attr == "expander"
                    and isinstance(no.func.value, ast.Name)
                    and no.func.value.id == "st"):
                continue
            argumentos = {k.arg: k.value for k in no.keywords}
            chave = argumentos.get("key")
            if isinstance(chave, ast.Constant) and chave.value.startswith("lce_a_painel_"):
                encontrados[chave.value] = argumentos
        self.assertEqual(set(encontrados), {
            "lce_a_painel_questoes", "lce_a_painel_mecanismo", "lce_a_painel_sintese"
        })
        for chave, kwargs in encontrados.items():
            with self.subTest(painel=chave):
                self.assertIsInstance(kwargs["on_change"], ast.Constant)
                self.assertEqual(kwargs["on_change"].value, "rerun")

    def test_legenda_antes_dos_paineis_nao_muda_estrutura_com_imposto_zero(self):
        """Impede regressão que desloca os expanders ao passar por t=0."""
        from pathlib import Path
        codigo = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        trecho = codigo.split('st.subheader("Experimento A · Quem suporta o imposto?")', 1)[1]
        trecho = trecho.split('# Roteiro opcional:', 1)[0]
        self.assertEqual(trecho.count('st.caption('), 1)
        self.assertIn('st.caption(aviso_tributo)', trecho)
        self.assertIn('if resultado["t"] == 0:', trecho)
        self.assertIn('elif not resultado["ha_transacoes"]:', trecho)
        self.assertIn('aviso_tributo = (', trecho)
        self.assertIn('else:', trecho)

    def test_questao_quantidade_nao_antecipa_conclusao(self):
        self.assertIn("acompanha as mudanças", QUESTOES["quantidade"])
        self.assertNotIn("permanecer igual", QUESTOES["quantidade"])

    def test_valida_questoes_e_niveis_invalidos(self):
        with self.assertRaises(ValueError):
            sugestao("inexistente", self.cenarios[20])
        with self.assertRaises(ValueError):
            explicacao("quantidade", "Eficiente", self.cenarios[20])
        with self.assertRaises(ValueError):
            formula("inexistente", "Matemática")


if __name__ == "__main__":
    unittest.main(verbosity=2)
