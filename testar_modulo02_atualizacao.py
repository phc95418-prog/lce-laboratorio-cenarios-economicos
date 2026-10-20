"""Contratos da rodada funcional/editorial; interface real tem evidência separada."""
import unittest
from copy import deepcopy
from modulo_02.formatacao_matematica import texto_matematico,latex_operadores
from modulo_02.textos_interface import perguntas_frequentes
from modulo_02.estado_individual import aplicar_evento
from modulo_02.estado_b import aplicar_evento_b,EstadoB,MODOS
from modulo_02.estado_comparacao import aplicar_quantidade
from modulo_02.analise_b import analise_b
from modulo_02.exportacao_pdf import validar_svg
from testar_modulo02_visual import interface,por_rotulo


class Apresentacao(unittest.TestCase):
    def test_indices_gregos_operadores_e_numeros_preservados(self):
        texto="Q_R=50,00; Q_M=26,67; RMg−CMg=−0,01; π=1.066,67."
        final=texto_matematico(texto)
        for alvo in ("$Q_R$","$Q_M$",r"$\mathrm{RMg}-\mathrm{CMg}$",r"$\pi$","−0,01","1.066,67"):
            self.assertIn(alvo,final)
        self.assertEqual(texto_matematico(final),final)
    def test_formulas_nao_duplicam_operadores_latex(self):
        f=r"\pi(Q)=RT(Q)-CT(Q);\quad RMg(Q)=CMg(Q)"
        uma=latex_operadores(f)
        self.assertIn(r"\mathrm{RMg}",uma)
        self.assertEqual(latex_operadores(uma),uma)
        self.assertEqual(latex_operadores("1.1537Q+26.67"),"1{,}1537Q+26{,}67")
    def test_relacao_lucro_excedente_condicional_sem_quarto_modo(self):
        dados=analise_b(EstadoB(modo=MODOS[2]))
        texto=" ".join(dados["propriedades"])
        self.assertIn("custos fixos agregados idênticos",texto)
        self.assertIn("+266,67",texto)
        self.assertIn(r"\Pi_M-\Pi_C",texto_matematico(texto))
        self.assertEqual(len(MODOS),3)
    def test_nove_perguntas_contextuais_sem_misturar_experimentos(self):
        a,b=(perguntas_frequentes(e) for e in ("A","B"))
        self.assertEqual((len(a),len(b)),(9,9))
        self.assertIn("Receita máxima",str(a));self.assertIn("ausência de comércio",str(b))
        self.assertNotIn("Como funciona a comparação do Experimento A?",[q for q,_ in b])
        self.assertIn("não cria sincronização",str(b))


class Consolidacao(unittest.TestCase):
    def test_a_live_nao_exibe_analise_anterior_e_fim_consolida(self):
        at=interface();e=at.session_state["m02_a_individual"]
        aplicar_evento(e,"q",dict(seq=1,fase="live",valor=40))
        at.run()
        self.assertEqual(at.metric[0].value,"40,00")
        self.assertEqual(len(at.tabs),0)
        self.assertTrue(any("texto anterior fica suspenso" in v.value for v in at.info))
        e=at.session_state["m02_a_individual"]
        aplicar_evento(e,"q",dict(seq=2,fase="fim",valor=40));at.run()
        self.assertEqual(len(at.tabs),3)
        self.assertEqual(at.session_state["m02_a_individual"].confirmado.q,40)
        self.assertFalse(at.exception)
    def test_b_live_calcula_e_fim_atualiza_texto(self):
        at=interface();at.segmented_control[0].set_value("Experimento B").run()
        e=at.session_state["m02_b_estado"]
        aplicar_evento_b(e,"a",dict(seq=1,fase="live",valor=120));at.run()
        self.assertEqual(at.metric[0].value,"50,00");self.assertEqual(len(at.tabs),0)
        e=at.session_state["m02_b_estado"]
        self.assertEqual(e.confirmado.a,100)
        aplicar_evento_b(e,"a",dict(seq=2,fase="fim",valor=120));at.run()
        self.assertEqual(at.session_state["m02_b_estado"].confirmado.a,120)
        self.assertEqual(len(at.tabs),3);self.assertFalse(at.exception)
    def test_quantidade_comparativa_consolidada_e_individual_independente(self):
        at=interface();por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        e=at.session_state["m02_a_individual"];antes=deepcopy(e.escolha)
        aplicar_quantidade(e,dict(seq=1,fase="live",valor=30.125));e.em_interacao=True;at.run()
        self.assertEqual(len(at.tabs),0)
        e=at.session_state["m02_a_individual"]
        aplicar_quantidade(e,dict(seq=2,fase="fim",valor=30.125));e.em_interacao=False;at.run()
        self.assertEqual(e.comparacao.q_confirmada,30.125)
        self.assertEqual(e.escolha,antes);self.assertEqual(len(at.tabs),3)
    def test_sobre_modelo_unico_na_lateral_em_a_e_b(self):
        at=interface()
        for exp in ("Experimento A","Experimento B"):
            at.segmented_control[0].set_value(exp).run()
            self.assertEqual(len([e for e in at.expander if e.label=="Sobre o modelo"]),1)
            self.assertEqual(len([e for e in at.sidebar.expander if e.label=="Sobre o modelo"]),1)
            self.assertFalse(at.exception)


class SVG(unittest.TestCase):
    def test_svg_valido_com_dimensoes_e_referencias_locais(self):
        self.assertEqual(validar_svg('<svg xmlns="http://www.w3.org/2000/svg" width="700" height="420"><path style="clip-path:url(#local)"/></svg>'),(700,420))
    def test_svg_malformado_ou_sem_dimensoes_rejeitado(self):
        for svg in ('','<html/>','<svg width="NaN" height="420"/>','<svg width="0" height="1"/>','<svg>'):
            with self.subTest(svg=svg),self.assertRaises(ValueError): validar_svg(svg)
    def test_svg_ativo_ou_externo_rejeitado(self):
        for filho in ('<script/>','<foreignObject/>','<image href="https://example.com/x.png"/>','<path onload="x()"/>','<path style="fill:url(https://example.com/x)"/>'):
            with self.subTest(filho=filho),self.assertRaises(ValueError):
                validar_svg('<svg width="700" height="420">'+filho+'</svg>')


if __name__=="__main__": unittest.main(verbosity=2)
