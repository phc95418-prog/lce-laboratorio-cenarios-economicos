"""Aceite de AC-01–10, EV-04–11, CA-01/03, V05 e AT-08."""

from copy import deepcopy
from dataclasses import replace
import unittest

from modulo_02.estado_individual import (
    Escolha, EstadoIndividual, aplicar_evento_sessao, confirmar,
)
from modulo_02.estado_comparacao import (
    aplicar_quantidade, dominio_comum, encerrar_comparacao, fixar_referencia,
    restaurar_parametros, resultados_comparacao, substituir_referencia,
    revalidar_comparacao,
)
from modulo_02.explicacoes_comparacao import sintese_comparacao, resumo_comparacao
from modulo_02.graficos_comparacao import graficos_comparacao
from modulo_02.validacao import ParametrosFirma


def iniciar(q=80,p=None):
    e = EstadoIndividual(escolha=Escolha(p or ParametrosFirma(),q))
    confirmar(e)
    fixar_referencia(e)
    return e


def parametro(e,campo,valor):
    sessao = {"m02_a_individual":e}
    aplicar_evento_sessao(sessao,0,campo,{"seq":e.sequencias.get(campo,0)+1,
                                      "fase":"campo","texto":str(valor)})


class EstadosComparacao(unittest.TestCase):
    def test_ev04_copia_cinco_parametros_sem_alterar_individual(self):
        e = iniciar(p=ParametrosFirma(a=120,b=1.1537,c=25,s=0.75,cf=450))
        self.assertEqual(e.comparacao.referencia,e.escolha.parametros)
        self.assertIsNot(e.comparacao.referencia,e.escolha.parametros)
        self.assertEqual((e.comparacao.q_fixa,e.escolha.q),(80,80))
        self.assertEqual(e.comparacao.perspectiva,"Quantidade fixa")
        parametro(e,"a",100)
        self.assertEqual(e.comparacao.referencia.a,120)

    def test_ev05_edicao_independente_e_precisao(self):
        e = iniciar()
        for i,q in enumerate((26.67,80/3),1):
            self.assertTrue(aplicar_quantidade(e,{"seq":i,"fase":"campo","texto":str(q)}))
            self.assertEqual(e.comparacao.q_fixa,q)
            self.assertEqual(e.escolha.q,80)

    def test_ev06_otimos_sao_derivados_e_nao_gravados(self):
        e = iniciar()
        parametro(e,"c",40)
        c = e.comparacao
        c.perspectiva = "Decisões ótimas"
        r,a,_ = resultados_comparacao(e)
        self.assertEqual(r.curvas.q,80/3)
        self.assertEqual(a.curvas.q,20)
        self.assertEqual((e.escolha.q,c.q_fixa),(80,80))
        c.perspectiva = "Quantidade fixa"
        r,a,_ = resultados_comparacao(e)
        self.assertEqual((r.curvas.q,a.curvas.q),(80,80))

    def test_ev07_08_at08_individual80_para30_nao_restaura(self):
        e = iniciar()
        aplicar_quantidade(e,{"seq":1,"fase":"campo","texto":"55"})
        referencia = e.comparacao.referencia
        parametro(e,"a",60)
        parametro(e,"b",2)
        self.assertEqual((e.escolha.q,e.comparacao.q_fixa),(30,30))
        self.assertTrue(e.aviso_dominio)
        self.assertTrue(e.comparacao.aviso)
        self.assertEqual(e.comparacao.referencia,referencia)
        parametro(e,"a",100)
        parametro(e,"b",1)
        self.assertEqual((e.escolha.q,e.comparacao.q_fixa),(30,30))
        encerrar_comparacao(e)
        self.assertEqual(e.escolha.q,30)
        self.assertIsNone(e.comparacao)

    def test_dominios_distintos_nao_limitam_individual_pela_referencia(self):
        e = iniciar(q=25,p=ParametrosFirma(a=60,b=2))
        parametro(e,"a",140)
        parametro(e,"b",0.5)
        # Na saída, a investigação individual pode usar todo o domínio atual.
        encerrar_comparacao(e)
        e.escolha = Escolha(e.escolha.parametros,200)
        fixar_referencia(e)
        # A referência menor só limita QF; QI já pertence ao cenário atual.
        e.comparacao.referencia = ParametrosFirma(a=60,b=2)
        parametro(e,"cf",400)
        self.assertEqual(e.escolha.q,200)
        self.assertEqual(e.comparacao.q_fixa,30)

    def test_ev09_restaurar_somente_atual_nao_busca_otimo(self):
        e = iniciar(q=110,p=ParametrosFirma(a=140,b=1,cf=300))
        ref = e.comparacao.referencia
        restaurar_parametros(e)
        self.assertEqual(e.escolha.parametros,ParametrosFirma())
        self.assertEqual(e.comparacao.referencia,ref)
        self.assertEqual((e.escolha.q,e.comparacao.q_fixa),(100,100))
        self.assertTrue(e.aviso_dominio)
        self.assertTrue(e.comparacao.aviso)

    def test_ev10_cancelamento_nao_altera_nada(self):
        e = iniciar(); parametro(e,"cf",400)
        antes = deepcopy(e)
        e.comparacao.substituindo = True
        substituir_referencia(e,False)
        self.assertEqual(e,antes)

    def test_ev10_confirmacao_substitui_so_referencia(self):
        e = iniciar(); parametro(e,"cf",400)
        antes = deepcopy(e)
        substituir_referencia(e,True)
        self.assertEqual(e.escolha,antes.escolha)
        self.assertEqual(e.comparacao.q_fixa,antes.comparacao.q_fixa)
        self.assertEqual(e.comparacao.referencia,e.escolha.parametros)
        self.assertEqual(resultados_comparacao(e)[2]["Lucro"],0)

    def test_ev11_nova_comparacao_nao_reusa_referencia_ou_perspectiva(self):
        e = iniciar(); e.comparacao.perspectiva="Decisões ótimas"
        parametro(e,"cf",400)
        encerrar_comparacao(e)
        self.assertEqual(e.escolha.parametros.cf,400)
        fixar_referencia(e)
        self.assertEqual(e.ciclo_comparacao,2)
        self.assertEqual(e.comparacao.perspectiva,"Quantidade fixa")
        self.assertEqual(e.comparacao.referencia.cf,400)

    def test_encerrar_preserva_perspectiva_foco_e_otimos_individuais(self):
        e = iniciar()
        e.perspectiva="Análise Marginal"
        e.foco="Lucro"
        e.mostrar_otimos=True
        e.comparacao.foco="Custo total"
        encerrar_comparacao(e)
        self.assertEqual((e.perspectiva,e.foco,e.mostrar_otimos),("Análise Marginal","Lucro",True))

    def test_campos_invalidos_e_eventos_atrasados_preservam_quantidades(self):
        e = iniciar()
        for i,texto in enumerate(("", "26,", "abc", "101", "-1", "nan"),1):
            self.assertFalse(aplicar_quantidade(e,{"seq":i,"fase":"campo","texto":texto}))
            self.assertEqual((e.escolha.q,e.comparacao.q_fixa),(80,80))
            self.assertTrue(e.comparacao.erro)
        self.assertFalse(aplicar_quantidade(e,{"seq":1,"fase":"campo","texto":"25"}))

    def test_texto_consolida_ao_fim_do_arraste(self):
        e = iniciar(q=25)
        sessao = {"m02_a_individual":e}
        aplicar_evento_sessao(sessao,0,"cf",{"seq":1,"fase":"live","valor":400})
        self.assertEqual(resultados_comparacao(e)[2]["Lucro"],-400)
        self.assertIn("coincidem",sintese_comparacao(e))
        aplicar_evento_sessao(sessao,0,"cf",{"seq":2,"fase":"fim","valor":400})
        self.assertIn("fixo aumentou",sintese_comparacao(e))

    def test_qf_confirmada_nao_se_altera_durante_live(self):
        e = iniciar(q=25)
        aplicar_quantidade(e,{"seq":1,"fase":"live","valor":50})
        self.assertEqual(resultados_comparacao(e)[0].curvas.q,50)
        self.assertEqual(resultados_comparacao(e,True)[0].curvas.q,25)
        aplicar_quantidade(e,{"seq":2,"fase":"fim","valor":50})
        self.assertEqual(resultados_comparacao(e,True)[0].curvas.q,50)

    def test_clamp_revalida_base_confirmada_durante_gesto(self):
        e = iniciar()
        aplicar_quantidade(e,{"seq":1,"fase":"live","valor":20})
        parametro(e,"a",60); parametro(e,"b",2)
        self.assertEqual(e.comparacao.q_fixa,20)
        r,a,_ = resultados_comparacao(e,True)
        self.assertEqual((r.curvas.q,a.curvas.q),(30,30))

    def test_evento_tardio_na_perspectiva_otima_nao_edita_qf(self):
        e = iniciar(); e.comparacao.perspectiva="Decisões ótimas"
        self.assertFalse(aplicar_quantidade(e,{"seq":1,"fase":"campo","texto":"20"}))
        self.assertEqual(e.comparacao.q_fixa,80)

    def test_hot_reload_comparacao_preserva_referencia_e_escolhas(self):
        from types import SimpleNamespace
        e = iniciar(); antigo = SimpleNamespace(**vars(e.comparacao))
        novo = revalidar_comparacao(antigo)
        self.assertEqual(novo,e.comparacao)

    def test_ciclo_integral_ev04_a_ev11(self):
        e = iniciar()
        parametro(e,"a",60); parametro(e,"b",2)
        aplicar_quantidade(e,{"seq":1,"fase":"campo","texto":"20"})
        e.comparacao.perspectiva="Decisões ótimas"
        r,a,_ = resultados_comparacao(e)
        self.assertAlmostEqual(r.curvas.q,80/3)
        self.assertEqual(a.curvas.q,8)
        e.comparacao.perspectiva="Quantidade fixa"
        restaurar_parametros(e)
        self.assertEqual((e.escolha.q,e.comparacao.q_fixa),(30,20))
        parametro(e,"cf",400)
        substituir_referencia(e,False)
        self.assertEqual(e.comparacao.referencia.cf,0)
        substituir_referencia(e,True)
        self.assertEqual(e.comparacao.referencia.cf,400)
        encerrar_comparacao(e)
        self.assertEqual(e.escolha,Escolha(ParametrosFirma(cf=400),30))


class ResultadosEGraficos(unittest.TestCase):
    def test_cf_isolado_c2_e_deltas_antes_de_formatar(self):
        e = iniciar(q=25); parametro(e,"cf",400)
        r,a,d = resultados_comparacao(e)
        self.assertEqual((r.curvas.receita_total,a.curvas.receita_total),(1875,1875))
        self.assertEqual((r.custo_total,a.custo_total),(812.5,1212.5))
        self.assertEqual((r.lucro,a.lucro),(1062.5,662.5))
        self.assertEqual(d,{"Quantidade":0,"Receita total":0,"Custo total":400,"Lucro":-400})
        parametro(e,"cf",400.000000001)
        self.assertNotEqual(resultados_comparacao(e)[2]["Lucro"],-400)

    def test_excecao_prioritaria_nao_apaga_sintese_de_variacao(self):
        e = iniciar(q=25); parametro(e,"cf",1600)
        self.assertIn("receita total é inferior",resumo_comparacao(e))
        self.assertIn("fixo aumentou",sintese_comparacao(e))
        self.assertNotIn("Erro",resumo_comparacao(e))

    def test_zero_nao_cria_preco_efetivo_e_mudanca_conjunta_permanece_consultavel(self):
        e = iniciar(q=0); parametro(e,"a",60); parametro(e,"c",120)
        self.assertIn("não existe preço efetivamente transacionado",resumo_comparacao(e))
        self.assertIn("simultâneas",sintese_comparacao(e))

    def test_diferencas_conjuntas_nao_imputam_cf_isolado(self):
        e = iniciar(); parametro(e,"cf",400); parametro(e,"a",120)
        self.assertIn("simultâneas",sintese_comparacao(e))
        self.assertNotIn("fixo aumentou",sintese_comparacao(e))

    def test_escalas_comuns_todos_focos_curvas_dominio_proprio(self):
        e = iniciar(q=25); parametro(e,"a",60); parametro(e,"b",2)
        for foco in ("Geral","Receita total","Custo total","Lucro"):
            e.comparacao.foco=foco
            figuras,_ = graficos_comparacao(e)
            self.assertEqual(figuras[0].layout.xaxis.range,figuras[1].layout.xaxis.range)
            self.assertEqual(figuras[0].layout.yaxis.range,figuras[1].layout.yaxis.range)
            self.assertEqual(figuras[0].layout.margin,figuras[1].layout.margin)
            for fig,limite in zip(figuras,(100,30)):
                for t in fig.data:
                    self.assertTrue(all(0 <= x <= limite for x in t.x))
                self.assertEqual(max(fig.data[0].x),limite)

    def test_g05_troca_perspectiva_preserva_escalas_e_contexto_zoom(self):
        e = iniciar(); parametro(e,"c",40)
        f,c = graficos_comparacao(e)
        e.comparacao.perspectiva="Decisões ótimas"
        g,d = graficos_comparacao(e)
        self.assertEqual(c,d)
        for a,b in zip(f,g):
            self.assertEqual(a.layout.xaxis.range,b.layout.xaxis.range)
            self.assertEqual(a.layout.yaxis.range,b.layout.yaxis.range)
            self.assertEqual(a.layout.uirevision,b.layout.uirevision)

    def test_destaques_e_fronteiras_sem_ordenada_de_outra_funcao(self):
        e = iniciar(); parametro(e,"c",120)
        e.comparacao.perspectiva="Decisões ótimas"
        e.comparacao.foco="Custo total"
        figuras,_ = graficos_comparacao(e)
        r,a,_ = resultados_comparacao(e)
        for fig,res in zip(figuras,(r,a)):
            marcadores=[t for t in fig.data if t.mode=="markers"]
            self.assertEqual(len(marcadores),1)
            self.assertEqual(marcadores[0].x[0],res.curvas.q)
            self.assertEqual(marcadores[0].y[0],res.custo_total)
        self.assertEqual(a.curvas.q,0)
        self.assertIsNone(a.preco_transacao)

    def test_restaurar_zoom_muda_contexto_sem_mudar_escolhas(self):
        e = iniciar(); antes = deepcopy(e)
        _,c = graficos_comparacao(e)
        e.comparacao.revisao += 1
        _,d = graficos_comparacao(e)
        self.assertNotEqual(c,d)
        e.comparacao.revisao=antes.comparacao.revisao
        self.assertEqual(e,antes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
