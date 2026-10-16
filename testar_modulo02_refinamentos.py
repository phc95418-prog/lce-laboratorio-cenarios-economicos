"""Regressões focadas: restauração, zoom, matemática e mensagens de A."""

import unittest

from modulo_02 import ParametrosFirma, avaliar_firma
from modulo_02.estado_individual import (
    Escolha, EstadoIndividual, alterar_zoom, aplicar_evento_sessao,
    chave_visualizacao, confirmar, restaurar_experimento, selecionar_otimo, selecionar_vista,
)
from modulo_02.explicacoes_individual import (
    GRUPOS_MATEMATICOS, TEXTO_PRECISAO, condicoes_excepcionais, resumo_economico, sintese,
)
from modulo_02.graficos_individual import grafico_individual


class Restauracao(unittest.TestCase):
    def test_restaura_estado_completo_e_nao_atinge_outras_areas(self):
        e = EstadoIndividual(escolha=Escolha(ParametrosFirma(a=120,b=1.1537,c=40,s=0.75,cf=1600),75),
                             perspectiva="Análise Marginal", foco="Lucro", mostrar_otimos=True,
                             interagiu=True, em_interacao=True, erros={"q":"inválido"},
                             sequencias={"q":9}, aviso_dominio="ajuste", zoom={"marginal":3})
        sessao = {"m02_a_individual":e,"m02_a_geracao":2,
                  "m02_a_controle_q_g2":{"evento":{"texto":"26,"}},
                  "m02_a_explicacao_g2":True,"m02_a_precisao_g2":True,
                  "m02_a_nivel_g2":"Matemática","m02_a_otimos_g2":True,
                  "modulo01":{"t":20},"futuro_b":{"a":60}}
        restaurar_experimento(sessao)
        self.assertEqual(sessao["m02_a_individual"],EstadoIndividual())
        self.assertIsNot(sessao["m02_a_individual"],e)
        self.assertEqual(sessao["m02_a_geracao"],3)
        self.assertEqual(set(sessao),{"m02_a_individual","m02_a_geracao","modulo01","futuro_b"})
        self.assertEqual(sessao["modulo01"],{"t":20})
        self.assertEqual(sessao["futuro_b"],{"a":60})

    def test_evento_atrasado_nao_reintroduz_rascunho_apos_restaurar(self):
        sessao = {"m02_a_individual":EstadoIndividual()}
        restaurar_experimento(sessao)
        self.assertFalse(aplicar_evento_sessao(sessao,0,"q",{"seq":99,"fase":"campo","texto":"75"}))
        self.assertEqual(sessao["m02_a_individual"].escolha.q,25)
        self.assertTrue(aplicar_evento_sessao(sessao,1,"q",{"seq":1,"fase":"campo","texto":"26,67"}))
        self.assertEqual(sessao["m02_a_individual"].escolha.q,26.67)

    def test_restauracoes_repetidas_geram_controles_novos(self):
        sessao = {}
        for geracao in range(1,4):
            restaurar_experimento(sessao)
            self.assertEqual(sessao["m02_a_geracao"],geracao)
            self.assertEqual(sessao["m02_a_individual"],EstadoIndividual())

    def test_ir_ao_otimo_preserva_parametros_vista_foco_e_zoom(self):
        p = ParametrosFirma(a=120,b=1.1537,cf=400)
        e = EstadoIndividual(escolha=Escolha(p,25),perspectiva="Análise Marginal",foco="Lucro",mostrar_otimos=True)
        alterar_zoom(e,"restaurar")
        selecionar_otimo(e)
        self.assertEqual(e.escolha.parametros,p)
        self.assertEqual(e.escolha.q,(120-20)/(2*1.1537+1))
        self.assertEqual((e.perspectiva,e.foco,e.mostrar_otimos),("Análise Marginal","Lucro",True))
        self.assertEqual(e.zoom,{"marginal":1})


class Zoom(unittest.TestCase):
    def test_gestos_habilitados_e_dominio_limitado(self):
        for p in (ParametrosFirma(), ParametrosFirma(a=60,b=2), ParametrosFirma(b=1.1537)):
            for q in (0,p.q_max/2,p.q_max):
                fig = grafico_individual(EstadoIndividual(escolha=Escolha(p,q)))
                self.assertEqual(fig.layout.dragmode,"zoom")
                self.assertFalse(fig.layout.xaxis.fixedrange)
                self.assertFalse(fig.layout.yaxis.fixedrange)
                self.assertEqual(fig.layout.xaxis.range,(0,p.q_max))
                self.assertEqual(fig.layout.xaxis.minallowed,0)
                self.assertEqual(fig.layout.xaxis.maxallowed,p.q_max)
                self.assertTrue(all(0 <= x <= p.q_max for t in fig.data for x in t.x))

    def test_restauracao_nao_muda_economia_curvas_ou_mensagens(self):
        from copy import deepcopy
        e = EstadoIndividual(escolha=Escolha(q=75),erros={"a":"entrada inválida"},aviso_dominio="ajuste")
        anterior = deepcopy(e)
        fig = grafico_individual(e)
        alterar_zoom(e,"restaurar")
        novo = grafico_individual(e)
        self.assertNotEqual(fig.layout.uirevision,novo.layout.uirevision)
        self.assertEqual(fig.data,novo.data)
        self.assertEqual(fig.layout.xaxis.range,novo.layout.xaxis.range)
        self.assertEqual(fig.layout.yaxis.range,novo.layout.yaxis.range)
        e.zoom = anterior.zoom
        self.assertEqual(e,anterior)

    def test_restauracao_independente_por_vista(self):
        e = EstadoIndividual(); alterar_zoom(e,"restaurar")
        selecionar_vista(e,"Resultados Totais","Lucro")
        alterar_zoom(e,"restaurar"); alterar_zoom(e,"restaurar")
        selecionar_vista(e,"Análise Marginal")
        alterar_zoom(e,"restaurar")
        self.assertEqual(e.zoom,{"totais:Geral":1,"totais:Lucro":2,"marginal":1})
        with self.assertRaises(ValueError):
            alterar_zoom(e,"ampliar")

    def test_vistas_e_parametros_possuem_enquadramentos_proprios(self):
        e = EstadoIndividual()
        base = grafico_individual(e)
        selecionar_vista(e,"Análise Marginal")
        marginal = grafico_individual(e)
        self.assertNotEqual(base.layout.uirevision,marginal.layout.uirevision)
        self.assertLessEqual(marginal.layout.yaxis.range[0],-100)
        e.escolha = Escolha(ParametrosFirma(a=60,b=2),25)
        novo = grafico_individual(e)
        self.assertNotEqual(marginal.layout.uirevision,novo.layout.uirevision)
        self.assertEqual(novo.layout.xaxis.range,(0,30))

    def test_revisao_plotly_nao_depende_da_quantidade(self):
        e = EstadoIndividual()
        antes = grafico_individual(e)
        e.escolha = Escolha(q=80/3)
        depois = grafico_individual(e)
        self.assertEqual(antes.layout.uirevision,depois.layout.uirevision)
        self.assertEqual(e.escolha.q,80/3)


class MensagensEMatematica(unittest.TestCase):
    def test_formulas_agrupadas_e_tolerancia_separada(self):
        self.assertEqual([titulo for titulo,_ in GRUPOS_MATEMATICOS],
                         ["Demanda e receita","Custos e lucro","Condições de maximização","Domínio e casos de fronteira"])
        formulas = " ".join(f for _,f in GRUPOS_MATEMATICOS)
        for trecho in ("a-bQ","aQ-bQ^2",r"\frac{s}{2}Q^2","CF+CV(Q)","c+sQ","RT(Q)-CT(Q)","2b+s"):
            self.assertIn(trecho,formulas)
        self.assertNotIn("10^{-12}",formulas)
        self.assertIn("sem piso absoluto",TEXTO_PRECISAO)
        self.assertIn("não nula",TEXTO_PRECISAO)

    def test_resumo_compacto_conserva_condicoes_no_aprofundamento(self):
        e = EstadoIndividual(escolha=Escolha(ParametrosFirma(cf=1600),100))
        confirmar(e)
        principal = resumo_economico(e)
        detalhes = " ".join(condicoes_excepcionais(e.escolha))
        self.assertIn("limite do domínio",principal)
        self.assertNotIn("receita total é inferior",principal)
        self.assertIn("receita total é inferior",detalhes)
        self.assertIn("não decide o fechamento",detalhes)
        self.assertNotIn("\n",principal)

    def test_lucro_negativo_nao_apaga_cf_isolado(self):
        e = EstadoIndividual(escolha=Escolha(ParametrosFirma(cf=1600),25))
        confirmar(e)
        self.assertIn("inferior",resumo_economico(e))
        self.assertIn("custo fixo aumentou",sintese(e))

    def test_resumo_q_zero_e_fronteiras(self):
        e = EstadoIndividual(escolha=Escolha(q=0))
        self.assertIn("sem transação",resumo_economico(e))
        e.escolha = Escolha(ParametrosFirma(c=100),0)
        self.assertIn("Não produzir maximiza",resumo_economico(e))
        e.escolha = Escolha(ParametrosFirma(c=120),25)
        self.assertIn("hipotética",resumo_economico(e))

    def test_sintese_nao_consolida_mudanca_marginal_durante_arraste(self):
        e = EstadoIndividual(escolha=Escolha(q=20),confirmado=Escolha(q=75),
                             anterior=Escolha(q=25),em_interacao=True,interagiu=True)
        self.assertIn("acima",resumo_economico(e))
        confirmar(e)
        self.assertIn("abaixo",resumo_economico(e))


if __name__ == "__main__":
    unittest.main(verbosity=2)
