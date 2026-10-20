"""Aceite ANA: relações verificáveis, fronteiras, precisão e consolidação."""
import unittest
from copy import deepcopy
from dataclasses import replace
from modulo_02.analise_experimento_a import analise_individual, analise_comparativa, analisar_resultado, variacao
from modulo_02.estado_individual import EstadoIndividual, Escolha, aplicar_evento, confirmar
from modulo_02.estado_comparacao import fixar_referencia, aplicar_quantidade
from modulo_02.validacao import ParametrosFirma
from modulo_02.modelo_firma import avaliar_firma

def texto(dados):
    return " ".join(" ".join(d[1]["leitura"]+d[1]["propriedades"]) for d in dados)

class Analises(unittest.TestCase):
    def test_estado_inicial_relacao_marginal_e_distincao_de_maximos(self):
        t=texto(analise_individual(EstadoIndividual()))
        for esperado in ("Q avaliada=25,00","RT=1.875,00","π=1.062,50","Q_R=50,00","Q_M=26,67","RMg−CMg=5,00","abaixo"):
            self.assertIn(esperado,t)

    def test_digitado_2667_nao_e_otimo_exato(self):
        e=EstadoIndividual(confirmado=Escolha(q=26.67))
        t=texto(analise_individual(e))
        self.assertIn("muito próxima",t)
        self.assertIn("RMg−CMg=-0,01",t)
        self.assertIn("não significa igualdade computacional",t)
        exato=texto(analise_individual(EstadoIndividual(confirmado=Escolha(q=80/3))))
        self.assertIn("Esta quantidade maximiza",exato)
        self.assertNotIn("muito próxima",exato)

    def test_zero_nao_equivale_a_otimo_positivo_minusculo(self):
        p=ParametrosFirma(c=100-1e-10)
        t=texto(analise_individual(EstadoIndividual(confirmado=Escolha(p,0))))
        self.assertIn("abaixo",t)
        self.assertNotIn("Esta quantidade maximiza",t)
        self.assertIn("a>c: Q_M é interior",t)
        self.assertNotIn("a=c: Q_M=0",t)

    def test_a_igual_c_distingue_igualdade_na_fronteira(self):
        p=ParametrosFirma(c=100,cf=100)
        t=texto(analise_individual(EstadoIndividual(confirmado=Escolha(p,0))))
        for esperado in ("a=c","RMg(0)=CMg(0)","não é ótimo interior","π(0)=−CF","sem preço realizado"):
            self.assertIn(esperado,t)

    def test_a_menor_c_nao_inventa_intersecao_ou_transacao(self):
        p=ParametrosFirma(c=120)
        t=texto(analise_individual(EstadoIndividual(confirmado=Escolha(p,0))))
        self.assertIn("RMg(0)<CMg(0)",t)
        self.assertIn("sem interseção marginal admissível",t)
        self.assertIn("sem preço realizado",t)
        t2=texto(analise_individual(EstadoIndividual(confirmado=Escolha(p,5))))
        self.assertIn("exploração hipotética",t2)
        self.assertIn("não maximiza",t2)

    def test_extremos_respeitam_direcao_admissivel(self):
        for q,direcao in ((0,"direita"),(100,"esquerda")):
            t=texto(analise_individual(EstadoIndividual(confirmado=Escolha(q=q))))
            self.assertIn("só há variações admissíveis para a "+direcao,t)
        self.assertIn("expansão além dele não é admissível",t)

    def test_lucro_negativo_nao_determina_fechamento(self):
        t=texto(analise_individual(EstadoIndividual(confirmado=Escolha(ParametrosFirma(cf=1600),25))))
        self.assertIn("inferior ao custo total",t)
        self.assertIn("não decide o fechamento",t)
        self.assertIn("custos de oportunidade",t)

    def test_cf_isolado_reproduz_identidades_para_qualquer_q(self):
        p=ParametrosFirma(); novo=replace(p,cf=100)
        self.assertIn("ΔCF=+100,00",variacao(p,novo))
        self.assertIn("Δπ=−ΔCF",variacao(p,novo))
        for q in (0,25,80/3,100):
            r,a=avaliar_firma(q,p),avaliar_firma(q,novo)
            self.assertAlmostEqual(a.custo_total-r.custo_total,100)
            self.assertAlmostEqual(a.lucro-r.lucro,-100)
            self.assertEqual(a.otimos.q_lucro,r.otimos.q_lucro)
            self.assertEqual(a.curvas.receita_total,r.curvas.receita_total)

    def test_c_isolado_sensibilidade_e_fronteira(self):
        p=ParametrosFirma()
        for c,quantidade in ((30,"23,33"),(100,"0,00"),(120,"0,00")):
            t=variacao(p,replace(p,c=c))
            self.assertIn("Variação isolada de c",t)
            self.assertIn("26,67 → "+quantidade,t)
            self.assertIn("∂Q_M/∂c=−1/(2b+s)<0",t)
            self.assertIn("fronteira",t)

    def test_sensibilidades_condicionais_restantes(self):
        p=ParametrosFirma()
        for k,v,formula in (("a",120,"∂Q_M/∂a=1/(2b+s)>0"),("b",2,"∂Q_M/∂b=−2(a−c)/(2b+s)²<0"),("s",2,"∂Q_M/∂s=−(a−c)/(2b+s)²<0")):
            self.assertIn(formula,variacao(p,replace(p,**{k:v})))

    def test_alteracoes_multiplas_nao_atribuem_efeito_isolado(self):
        t=variacao(ParametrosFirma(),ParametrosFirma(a=120,c=30,cf=100))
        self.assertIn("Mudanças simultâneas em a, c, CF",t)
        self.assertIn("Não há decomposição",t)
        self.assertNotIn("Variação isolada",t)

    def test_texto_individual_aguarda_fim_de_interacao(self):
        e=EstadoIndividual();antes=analise_individual(e)
        aplicar_evento(e,"c",{"seq":1,"fase":"live","valor":30})
        self.assertEqual(analise_individual(e),antes)
        aplicar_evento(e,"c",{"seq":2,"fase":"fim","valor":30})
        self.assertIn("Variação isolada de c",texto(analise_individual(e)))
        self.assertEqual(e.anterior.parametros.c,20)

    def test_equacoes_substituem_parametros_com_precisao_interna(self):
        p=ParametrosFirma(a=120,b=1.1537,c=30,s=.75,cf=100)
        formulas=str(analisar_resultado(avaliar_firma(25,p))["formulas"])
        for esperado in ("120","1.1537","30","0.75","100"):
            self.assertIn(esperado,formulas)
        self.assertNotIn("1.15)",formulas)

    def test_comparacao_mesmo_q_e_delta_assinado(self):
        e=EstadoIndividual();fixar_referencia(e)
        e.escolha=Escolha(ParametrosFirma(cf=100),25);confirmar(e)
        antes=deepcopy(e);t=texto(analise_comparativa(e))
        for esperado in ("Referência congelada → Atual","ambos avaliados em QF=25,00","ΔCT=+100,00","Δπ=−100,00","domínio comum"):
            self.assertIn(esperado,t)
        self.assertEqual(e,antes)

    def test_comparacao_otimos_distintos_nao_imputa_delta_a_mesmo_q(self):
        e=EstadoIndividual();fixar_referencia(e)
        e.escolha=Escolha(ParametrosFirma(c=30),25);confirmar(e)
        e.comparacao.perspectiva="Decisões ótimas"
        antes=deepcopy(e);t=texto(analise_comparativa(e))
        for esperado in ("Referência=26,67","Atual=23,33","Não são efeitos a Q constante","ΔQ=−3,33"):
            self.assertIn(esperado,t)
        self.assertEqual(e,antes)

    def test_comparacao_aguarda_confirmacao_de_q_e_parametros(self):
        e=EstadoIndividual();fixar_referencia(e);antes=analise_comparativa(e)
        aplicar_quantidade(e,{"seq":1,"fase":"live","valor":30.125})
        self.assertEqual(analise_comparativa(e),antes)
        aplicar_quantidade(e,{"seq":2,"fase":"fim","valor":30.125})
        self.assertIn("QF=30,12",texto(analise_comparativa(e)))
        antes=analise_comparativa(e)
        aplicar_evento(e,"c",{"seq":1,"fase":"live","valor":30})
        self.assertEqual(analise_comparativa(e),antes)
        aplicar_evento(e,"c",{"seq":2,"fase":"fim","valor":30})
        self.assertIn("Variação isolada de c",texto(analise_comparativa(e)))

if __name__=="__main__":
    unittest.main(verbosity=2)
