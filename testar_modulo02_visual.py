"""Integração das Fases A/B; abrir/fechar e cores reais exigem navegador."""

import unittest
import sys
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from modulo_02.estado_individual import Escolha, EstadoIndividual
from modulo_02.validacao import ParametrosFirma
from modulo_02.graficos_individual import grafico_individual


def interface():
    # Cada AppTest cria um Runtime isolado; registros V2 de outro Runtime
    # não sobrevivem, embora o cache de módulos Python sobreviva no teste.
    for nome in ("modulo_02.interface_individual","modulo_02.interface_comparacao","modulo_02.interface_b","modulo_02.estrutura_visual"):
        sys.modules.pop(nome,None)
    return AppTest.from_file("lce_modulo02.py",default_timeout=15).run()


def por_rotulo(elementos,rotulo):
    return next(x for x in elementos if x.label == rotulo)


class IntegracaoVisual(unittest.TestCase):
    def test_analise_opcional_sem_roteiro_e_zoom_nao_altera_economia(self):
        at=interface()
        self.assertNotIn("Ideias para investigar · opcional",[e.label for e in at.expander])
        self.assertNotIn("Compreenda o mecanismo · opcional",[e.label for e in at.expander])
        self.assertFalse(por_rotulo(at.expander,"Análise econômica e matemática").proto.expanded)
        self.assertEqual([t.label for t in at.tabs],
                         ["Leitura econômica","Estrutura matemática","Propriedades e limites"])
        por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        antes=deepcopy(at.session_state["m02_a_individual"])
        self.assertEqual(por_rotulo(at.radio,"Zoom comparativo").value,"Sincronizado")
        por_rotulo(at.radio,"Zoom comparativo").set_value("Independente").run()
        self.assertEqual(at.session_state["m02_a_individual"],antes)
        por_rotulo(at.radio,"Zoom comparativo").set_value("Sincronizado").run()
        self.assertEqual(at.session_state["m02_a_individual"],antes)
        self.assertEqual([t.label for t in at.tabs],
                         ["Leitura econômica","Estrutura matemática","Propriedades e limites"])
        self.assertFalse(at.exception)

    def test_inicial_quatro_paineis_e_acoes_exclusivas_na_lateral(self):
        at=interface()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.get("popover")),4)
        self.assertEqual([b.label for b in at.sidebar.button],
                         ["Restaurar experimento","Fixar cenário de referência"])
        self.assertEqual(len([b for b in at.button if b.label=="Fixar cenário de referência"]),1)
        self.assertEqual([m.value for m in at.metric],["25,00","75,00","1.875,00","812,50","1.062,50"])

    def test_perspectiva_e_foco_preservam_precisao_e_parametros(self):
        at=interface()
        e=at.session_state["m02_a_individual"]
        e.escolha=Escolha(ParametrosFirma(b=1.1537),80/3)
        antes=e.escolha
        at.run()
        por_rotulo(at.radio,"Foco do gráfico").set_value("Lucro").run()
        por_rotulo(at.radio,"Perspectiva").set_value("Análise Marginal").run()
        self.assertFalse(at.exception)
        self.assertNotIn("Foco do gráfico",[x.label for x in at.radio])
        self.assertEqual(at.session_state["m02_a_individual"].escolha,antes)
        por_rotulo(at.radio,"Perspectiva").set_value("Resultados Totais").run()
        self.assertEqual(por_rotulo(at.radio,"Foco do gráfico").value,"Lucro")
        self.assertEqual(at.session_state["m02_a_individual"].escolha,antes)

    def test_restauracao_pela_lateral_reinicia_individual(self):
        at=interface()
        e=at.session_state["m02_a_individual"]
        e.escolha=Escolha(ParametrosFirma(cf=1600),80/3)
        e.erros={"a":"entrada inválida"}
        e.mostrar_otimos=True
        e.zoom={"totais:Geral":2}
        at.run()
        por_rotulo(at.sidebar.button,"Restaurar experimento").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m02_a_individual"],EstadoIndividual())
        self.assertEqual(at.session_state["m02_a_geracao"],1)

    def test_comparacao_preserva_controles_e_retorno(self):
        at=interface()
        por_rotulo(at.radio,"Perspectiva").set_value("Análise Marginal").run()
        por_rotulo(at.checkbox,"Mostrar pontos ótimos").check().run()
        escolha=at.session_state["m02_a_individual"].escolha
        por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        self.assertFalse(at.exception)
        for rotulo in ("Substituir referência","Restaurar parâmetros do Atual","Encerrar comparação"):
            self.assertIn(rotulo,[x.label for x in at.button])
        self.assertNotIn("Ir para lucro máximo",[x.label for x in at.button])
        por_rotulo(at.radio,"Perspectiva comparativa").set_value("Decisões ótimas").run()
        self.assertEqual(at.session_state["m02_a_individual"].escolha,escolha)
        por_rotulo(at.button,"Encerrar comparação").click().run()
        self.assertEqual(len(at.get("popover")),4)
        self.assertEqual(por_rotulo(at.radio,"Perspectiva").value,"Análise Marginal")
        self.assertTrue(por_rotulo(at.checkbox,"Mostrar pontos ótimos").value)

    def test_comparacao_quatro_paineis_acoes_na_lateral_e_q_independentes(self):
        at=interface()
        por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        e=at.session_state["m02_a_individual"]
        e.comparacao.q_fixa=e.comparacao.q_confirmada=30.125
        e.escolha=Escolha(ParametrosFirma(cf=100),25)
        antes=deepcopy(e)
        at.run()
        self.assertEqual(len(at.get("popover")),4)
        self.assertEqual([b.label for b in at.sidebar.button],
                         ["Substituir referência","Restaurar parâmetros do Atual","Encerrar comparação"])
        por_rotulo(at.radio,"Foco dos dois gráficos").set_value("Lucro").run()
        por_rotulo(at.radio,"Perspectiva comparativa").set_value("Decisões ótimas").run()
        e=at.session_state["m02_a_individual"]
        self.assertEqual(e.escolha,antes.escolha)
        self.assertEqual(e.comparacao.q_fixa,30.125)
        self.assertEqual(e.comparacao.referencia,antes.comparacao.referencia)
        self.assertEqual(e.comparacao.foco,"Lucro")
        por_rotulo(at.radio,"Perspectiva comparativa").set_value("Quantidade fixa").run()
        self.assertEqual(at.session_state["m02_a_individual"].comparacao.q_fixa,30.125)
        self.assertFalse(at.exception)

    def test_confirmacao_cancelamento_e_restauracao_somente_atual(self):
        at=interface()
        por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        e=at.session_state["m02_a_individual"]
        e.escolha=Escolha(ParametrosFirma(cf=100),25)
        at.run()
        original=e.comparacao.referencia
        por_rotulo(at.sidebar.button,"Substituir referência").click().run()
        self.assertTrue(at.session_state["m02_a_individual"].comparacao.substituindo)
        por_rotulo(at.sidebar.button,"Cancelar substituição").click().run()
        self.assertEqual(at.session_state["m02_a_individual"].comparacao.referencia,original)
        por_rotulo(at.sidebar.button,"Substituir referência").click().run()
        por_rotulo(at.sidebar.button,"Confirmar substituição").click().run()
        self.assertEqual(at.session_state["m02_a_individual"].comparacao.referencia.cf,100)
        por_rotulo(at.sidebar.button,"Restaurar parâmetros do Atual").click().run()
        self.assertEqual(at.session_state["m02_a_individual"].escolha.parametros.cf,0)
        self.assertEqual(at.session_state["m02_a_individual"].comparacao.referencia.cf,100)
        self.assertFalse(at.exception)


class Marcadores(unittest.TestCase):
    def test_formas_e_contornos_sem_mudar_coordenadas_ou_economia(self):
        e=EstadoIndividual(mostrar_otimos=True)
        antes=deepcopy(e)
        fig=grafico_individual(e)
        pontos=[t for t in fig.data if t.meta and t.meta.get("papel")=="otimo"]
        self.assertEqual([t.marker.symbol for t in pontos],["diamond","x"])
        self.assertEqual([t.x[0] for t in pontos],[50,80/3])
        self.assertEqual([t.y[0] for t in pontos],[2500,3200/3])
        for t in pontos:
            self.assertEqual(t.marker.color,"#ffffff")
            self.assertEqual(t.marker.line.color,"#0f172a")
            self.assertGreaterEqual(t.marker.line.width,2)
        self.assertEqual(e,antes)

    def test_contraste_nao_textual_duplo_nos_fundos_nativos(self):
        def luminancia(hexadecimal):
            valores=[int(hexadecimal[i:i+2],16)/255 for i in (1,3,5)]
            linear=[c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4 for c in valores]
            return sum(x*w for x,w in zip(linear,(0.2126,0.7152,0.0722)))
        def contraste(a,b):
            l=sorted((luminancia(a),luminancia(b)))
            return (l[1]+0.05)/(l[0]+0.05)
        self.assertGreater(contraste("#0f172a","#ffffff"),3)
        self.assertGreater(contraste("#ffffff","#0e1117"),3)

    def test_guias_em_custo_e_fronteira_marginal_tem_contorno_duplo(self):
        for e in (EstadoIndividual(foco="Custo total",mostrar_otimos=True),
                  EstadoIndividual(escolha=Escolha(ParametrosFirma(c=120),25),
                                   perspectiva="Análise Marginal",mostrar_otimos=True)):
            fig=grafico_individual(e)
            guias=[s for s in fig.layout.shapes if s.line.color in ("#ffffff","#0f172a")]
            self.assertTrue(guias)
            for fundo,frente in zip(guias[::2],guias[1::2]):
                self.assertEqual((fundo.x0,fundo.x1),(frente.x0,frente.x1))
                self.assertGreater(fundo.line.width,frente.line.width)


if __name__ == "__main__":
    unittest.main(verbosity=2)
