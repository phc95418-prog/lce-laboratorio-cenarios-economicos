"""Aceite B: motor existente, polígonos, estados, narrativas e integração local."""
import unittest
from copy import deepcopy
from dataclasses import replace
from math import isclose
from modulo_02.estado_b import *
from modulo_02.estado_individual import EstadoIndividual, Escolha
from modulo_02.validacao import ParametrosFirma
from modulo_02.estruturas_mercado import avaliar_mercados
from modulo_02.geometria_b import poligono_b, area_poligono
from modulo_02.graficos_b import grafico_b
from modulo_02.analise_b import analise_b
from testar_modulo02_visual import interface, por_rotulo

class EstadosB(unittest.TestCase):
    def test_padrao_independente_com_quatro_parametros(self):
        e=EstadoB()
        self.assertEqual(e.modo,"Comparar resultados")
        self.assertEqual((e.regiao,e.regime,e.decomposicao),("EC","Concorrência",False))
        self.assertFalse(hasattr(e.parametros,"cf"))
    def test_importacao_pontual_exclui_cf_e_nao_modifica_a(self):
        a=EstadoIndividual(escolha=Escolha(ParametrosFirma(a=120,b=1.1537,c=30,s=.75,cf=1600),25))
        antes=deepcopy(a);b=EstadoB()
        self.assertTrue(importar_de_a(b,a))
        self.assertEqual(b.parametros,ParametrosMercado(120,1.1537,30,.75))
        self.assertEqual(a,antes)
        a.escolha=Escolha(ParametrosFirma(a=60),25)
        self.assertEqual(b.parametros.a,120)
        self.assertFalse(hasattr(b.parametros,"cf"))
    def test_origem_ausente_nao_inventa_valores(self):
        b=EstadoB(parametros=ParametrosMercado(a=120))
        antes=b.parametros
        self.assertFalse(importar_de_a(b,None));self.assertEqual(b.parametros,antes)
        self.assertIn("indisponíveis",b.aviso)
    def test_campo_entre_ticks_precisao_e_rejeicao(self):
        b=EstadoB()
        aplicar_evento_b(b,"b",{"seq":1,"fase":"campo","texto":"1,1537"})
        self.assertEqual(b.parametros.b,1.1537)
        for seq,valor in ((2,"2.01"),(3,"-"),(4,"NaN")):
            aplicar_evento_b(b,"b",{"seq":seq,"fase":"invalido","texto":valor})
            self.assertEqual(b.parametros.b,1.1537);self.assertIn("b",b.erros)
    def test_eventos_invalidos_e_atrasados(self):
        b=EstadoB();antes=deepcopy(b)
        for campo,evento in (("cf",{"seq":1,"fase":"campo","texto":"100"}),("a",{"seq":True,"fase":"live","valor":120}),("a",{})):
            self.assertFalse(aplicar_evento_b(b,campo,evento));self.assertEqual(b,antes)
        aplicar_evento_b(b,"a",{"seq":1,"fase":"campo","texto":"120"})
        self.assertFalse(aplicar_evento_b(b,"a",{"seq":1,"fase":"fim","valor":100}))
        self.assertEqual(b.parametros.a,120)
    def test_analise_aguarda_fim_sem_atrasar_resultados(self):
        b=EstadoB();antes=analise_b(b)
        aplicar_evento_b(b,"a",{"seq":1,"fase":"live","valor":120})
        self.assertEqual(avaliar_mercados(b.parametros).concorrencia.curvas.q,50)
        self.assertEqual(analise_b(b),antes)
        aplicar_evento_b(b,"a",{"seq":2,"fase":"fim","valor":120})
        self.assertNotEqual(analise_b(b),antes);self.assertEqual(b.anterior.a,100)
    def test_dwl_nao_apaga_regime_e_decomposicao_restaura_exatamente(self):
        b=EstadoB(modo=MODOS[2],regiao="EP",regime="Monopólio")
        abrir_decomposicao(b)
        self.assertEqual((b.parcela,b.selecao_guardada),("DWL",("EP","Monopólio")))
        for area in PARCELAS:
            b.parcela=area;self.assertEqual(regiao_ativa(b),area)
        abrir_decomposicao(b)
        fechar_decomposicao(b)
        self.assertEqual((b.regiao,b.regime,b.decomposicao),("EP","Monopólio",False))
        b.regiao="DWL";self.assertEqual(b.regime,"Monopólio")
    def test_restauracao_preserva_selecoes(self):
        b=EstadoB(parametros=ParametrosMercado(a=120),modo=MODOS[2],regime="Monopólio",regiao="EP",roda=True)
        abrir_decomposicao(b);b.parcela="T"
        restaurar_parametros_b(b)
        self.assertEqual(b.parametros,ParametrosMercado())
        self.assertEqual((b.modo,b.parcela,b.regime,b.decomposicao,b.roda),(MODOS[2],"T","Monopólio",True,True))

class GeometriaB(unittest.TestCase):
    def test_referencia_numerica_e_identidades(self):
        r=avaliar_mercados(ParametrosMercado())
        for real,esperado in ((r.concorrencia.curvas.q,40),(r.monopolio.curvas.q,80/3),
            (r.concorrencia.preco_transacao,60),(r.monopolio.preco_transacao,220/3),
            (r.concorrencia.curvas.excedente_consumidor,800),(r.concorrencia.curvas.excedente_produtor,800),
            (r.monopolio.curvas.excedente_consumidor,3200/9),(r.monopolio.curvas.excedente_produtor,3200/3),
            (r.decomposicao.peso_morto,1600/9),(r.diferencas.quantidade.percentual,-100/3),
            (r.diferencas.preco.percentual,200/9)):
            self.assertTrue(isclose(real,esperado,abs_tol=1e-9,rel_tol=1e-9))
    def test_areas_poligonais_conferem_com_integrais_em_grade(self):
        for a in (60,100,140):
            for b in (.5,1.1537,2):
                for s in (.25,1,3):
                    p=ParametrosMercado(a,b,20,s);r=avaliar_mercados(p)
                    for regime,resultado in zip(REGIMES,(r.concorrencia,r.monopolio)):
                        for area,valor in (("EC",resultado.curvas.excedente_consumidor),("EP",resultado.curvas.excedente_produtor)):
                            with self.subTest(p=p,regime=regime,area=area):
                                self.assertTrue(isclose(area_poligono(poligono_b(p,area,regime)),valor,abs_tol=1e-9,rel_tol=1e-9))
                    for area,valor in (("DWL",r.decomposicao.peso_morto),("T",r.decomposicao.transferencia),("L_C",r.decomposicao.perda_consumidor),("L_P",r.decomposicao.perda_produtor)):
                        self.assertTrue(isclose(area_poligono(poligono_b(p,area)),valor,abs_tol=1e-9,rel_tol=1e-9))
    def test_vertices_normativos_t_lc_lp(self):
        p=ParametrosMercado();qm=80/3;qc=40;pc=60;pm=220/3;cm=140/3
        esperados={"T":[(0,pc),(qm,pc),(qm,pm),(0,pm)],"L_C":[(qm,pm),(qm,pc),(qc,pc)],"L_P":[(qm,pc),(qm,cm),(qc,pc)]}
        for area,vertices in esperados.items():
            for obtido,esperado in zip(poligono_b(p,area),vertices):
                for x,y in zip(obtido,esperado): self.assertAlmostEqual(x,y,places=10)
    def test_inclinacoes_desiguais_nao_dividem_perda_igualmente(self):
        p=ParametrosMercado(b=2,s=.25);r=avaliar_mercados(p)
        for area,valor in (("T",629.91157247),("L_C",279.96069888),("L_P",34.99508736),("DWL",314.95578624)):
            self.assertAlmostEqual(area_poligono(poligono_b(p,area)),valor,places=7)
        self.assertNotEqual(r.decomposicao.perda_consumidor,r.decomposicao.perda_produtor)
        self.assertAlmostEqual(r.decomposicao.peso_morto,r.decomposicao.perda_consumidor+r.decomposicao.perda_produtor)
    def test_fronteiras_sem_comercio_precos_percentuais_ou_areas(self):
        for c in (100,120,160):
            p=ParametrosMercado(c=c);r=avaliar_mercados(p)
            self.assertIsNone(r.concorrencia.preco_transacao);self.assertIsNone(r.monopolio.preco_transacao)
            self.assertIsNone(r.diferencas.quantidade.percentual);self.assertIsNone(r.diferencas.preco.percentual)
            for area in ("EC","EP","DWL","T","L_C","L_P"): self.assertEqual(poligono_b(p,area),[])
            for resultado in (r.concorrencia,r.monopolio):
                self.assertEqual((resultado.curvas.q,resultado.curvas.excedente_consumidor,resultado.curvas.excedente_produtor,resultado.curvas.excedente_total),(0,0,0,0))
    def test_apenas_uma_regiao_e_uma_figura_com_dominio_valido(self):
        for area in ("EC","EP","DWL","T","L_C","L_P"):
            e=EstadoB(modo=MODOS[2],regiao=area if area in REGIOES else "EC",decomposicao=area not in REGIOES,parcela=area)
            fig=grafico_b(e)
            preenchimentos=[t for t in fig.data if t.fill=="toself"]
            self.assertEqual(len(preenchimentos),1)
            self.assertEqual(preenchimentos[0].meta["regiao"],area)
            for t in fig.data:
                self.assertTrue(all(0<=q<=e.parametros.q_max for q in t.x))
    def test_marcadores_c_e_m_sobre_demanda_e_condicao_marginal_distinta(self):
        for modo in MODOS[:2]:
            fig=grafico_b(EstadoB(modo=modo))
            pontos=[t for t in fig.data if t.meta.get("papel")=="equilibrio"]
            self.assertEqual(len(pontos),2)
            for t in pontos: self.assertAlmostEqual(t.y[0],100-t.x[0])
            marginais=[t for t in fig.data if t.meta.get("papel")=="condicao_marginal"]
            if modo==MODOS[1]:
                self.assertAlmostEqual(marginais[0].y[0],140/3)
                self.assertAlmostEqual(pontos[1].y[0],220/3)
    def test_eixos_e_revisao_nao_mudam_com_regime_regiao_ou_decomposicao(self):
        e=EstadoB(modo=MODOS[2]);base=grafico_b(e)
        for regime in REGIMES:
            for area in REGIOES:
                e.regime=regime;e.regiao=area
                fig=grafico_b(e)
                self.assertEqual(fig.layout.xaxis.range,base.layout.xaxis.range)
                self.assertEqual(fig.layout.yaxis.range,base.layout.yaxis.range)
                self.assertEqual(fig.layout.uirevision,base.layout.uirevision)
        abrir_decomposicao(e)
        self.assertEqual(grafico_b(e).layout.uirevision,base.layout.uirevision)
    def test_fronteiras_nao_criam_pontos_ficticios(self):
        for c in (100,120):
            for modo in MODOS:
                e=EstadoB(parametros=ParametrosMercado(c=c),modo=modo)
                fig=grafico_b(e)
                self.assertFalse(any(t.meta.get("papel")=="equilibrio" for t in fig.data))
                self.assertFalse(any(t.fill=="toself" for t in fig.data))
    def test_marginal_inclui_rmg_negativa_sem_extrapolar_demanda(self):
        fig=grafico_b(EstadoB(modo=MODOS[1]))
        rmg=next(t for t in fig.data if t.meta.get("funcao")=="receita_marginal")
        self.assertAlmostEqual(rmg.y[-1],-100)
        self.assertLess(fig.layout.yaxis.range[0],-100)

class AnaliseB(unittest.TestCase):
    def test_narrativas_proprias_dos_tres_modos(self):
        for modo,termo in zip(MODOS,("regra de decisão","internaliza","Região ativa")):
            e=EstadoB(modo=modo);antes=deepcopy(e);dados=analise_b(e)
            self.assertIn(termo," ".join(dados["leitura"]))
            self.assertEqual(e,antes)
            self.assertNotIn("Ideias para investigar",str(dados))
    def test_fronteira_igualdade_diferente_de_sem_intersecao(self):
        for c,termo in ((100,"igualdade na fronteira"),(120,"não há interseção")):
            e=EstadoB(confirmado=ParametrosMercado(c=c),modo=MODOS[1])
            t=str(analise_b(e))
            self.assertIn(termo,t);self.assertIn("não aplicável",t)
            self.assertIn("não demonstra equivalência econômica geral",t)
    def test_decomposicao_contextual_e_hipoteses_de_bem_estar(self):
        e=EstadoB(confirmado=ParametrosMercado(b=2,s=.25),modo=MODOS[2])
        abrir_decomposicao(e);e.parcela="T"
        t=str(analise_b(e))
        for esperado in ("Região ativa: T","não é perda líquida","b≠s","não automaticamente lucro","efeitos-renda"):
            self.assertIn(esperado,t)
    def test_alteracoes_multiplas_nao_inventam_decomposicao_causal(self):
        e=EstadoB(confirmado=ParametrosMercado(a=120,c=30))
        self.assertIn("mudanças simultâneas em a, c",str(analise_b(e)))
        self.assertIn("120",str(analise_b(e)["formulas"]))

class IntegracaoB(unittest.TestCase):
    def b(self):
        at=interface();por_rotulo(at.segmented_control,"Experimento").set_value("Experimento B").run()
        self.assertFalse(at.exception)
        return at
    def test_entrada_padrao_cinco_paineis_e_resultados(self):
        at=self.b()
        self.assertEqual(len(at.get("popover")),5)
        self.assertEqual([m.value for m in at.metric],["40,00","60,00","26,67","73,33"])
        self.assertEqual(por_rotulo(at.radio,"Modo do Experimento B").value,MODOS[0])
        self.assertNotIn("Regime para a região",[x.label for x in at.radio])
    def test_bem_estar_decomposicao_e_regime_guardado(self):
        at=self.b();por_rotulo(at.radio,"Modo do Experimento B").set_value(MODOS[2]).run()
        self.assertEqual(por_rotulo(at.radio,"Região principal").value,"EC")
        por_rotulo(at.radio,"Regime para a região").set_value("Monopólio").run()
        por_rotulo(at.checkbox,"Examinar origem da perda de eficiência").check().run()
        self.assertEqual(por_rotulo(at.radio,"Região da decomposição").value,"DWL")
        self.assertNotIn("Região principal",[x.label for x in at.radio])
        self.assertNotIn("Regime para a região",[x.label for x in at.radio])
        por_rotulo(at.radio,"Região da decomposição").set_value("L_P").run()
        por_rotulo(at.checkbox,"Examinar origem da perda de eficiência").uncheck().run()
        self.assertEqual(por_rotulo(at.radio,"Região principal").value,"EC")
        self.assertEqual(por_rotulo(at.radio,"Regime para a região").value,"Monopólio")
        por_rotulo(at.radio,"Região principal").set_value("DWL").run()
        self.assertNotIn("Regime para a região",[x.label for x in at.radio])
        por_rotulo(at.radio,"Região principal").set_value("EP").run()
        self.assertEqual(por_rotulo(at.radio,"Regime para a região").value,"Monopólio")
        self.assertFalse(at.exception)
    def test_navegacao_preserva_a_comparacao_e_b_sem_importacao_automatica(self):
        at=interface()
        a=at.session_state["m02_a_individual"]
        a.escolha=Escolha(ParametrosFirma(a=120,cf=1600),25);a.confirmado=a.escolha
        at.run();por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        antes=deepcopy(at.session_state["m02_a_individual"])
        por_rotulo(at.segmented_control,"Experimento").set_value("Experimento B").run()
        self.assertEqual(at.session_state["m02_b_estado"].parametros.a,100)
        por_rotulo(at.sidebar.button,"Utilizar parâmetros do Experimento A").click().run()
        self.assertEqual(at.session_state["m02_b_estado"].parametros.a,120)
        por_rotulo(at.radio,"Modo do Experimento B").set_value(MODOS[1]).run()
        por_rotulo(at.segmented_control,"Experimento").set_value("Experimento A").run()
        self.assertEqual(at.session_state["m02_a_individual"],antes)
        por_rotulo(at.segmented_control,"Experimento").set_value("Experimento B").run()
        self.assertEqual(at.session_state["m02_b_estado"].modo,MODOS[1])
        self.assertEqual(at.session_state["m02_b_estado"].parametros.a,120)
        self.assertFalse(at.exception)
    def test_nova_sessao_reinicia_a_e_b(self):
        at=self.b();por_rotulo(at.radio,"Modo do Experimento B").set_value(MODOS[2]).run()
        nova=interface();self.assertEqual(nova.session_state["m02_a_individual"].escolha.q,25)
        por_rotulo(nova.segmented_control,"Experimento").set_value("Experimento B").run()
        self.assertEqual(nova.session_state["m02_b_estado"],EstadoB())

if __name__=="__main__": unittest.main(verbosity=2)
