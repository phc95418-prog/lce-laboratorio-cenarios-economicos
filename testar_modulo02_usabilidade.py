"""Aceite da revisão visual: navegação, ajuda e nomenclatura sem efeitos econômicos."""
import unittest
from copy import deepcopy

import streamlit as st
from testar_modulo02_visual import interface, por_rotulo
from modulo_02.textos_interface import FAQ, REGIOES
from modulo_02.estado_b import MODOS


class Usabilidade(unittest.TestCase):
    def test_hierarquia_identidade_e_seletor_nativo(self):
        at=interface()
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value,"Módulo 02 · Decisões da Firma")
        self.assertEqual(at.caption[0].value,"LCE · LABORATÓRIO DE CENÁRIOS ECONÔMICOS")
        self.assertEqual(at.segmented_control[0].value,"Experimento A")
        self.assertIn("**Experimento A · Decisão de produção da firma monopolista**",[m.value for m in at.markdown])
        self.assertEqual(st.get_option("client.toolbarMode"),"viewer")

    def test_ajuda_opcional_compartilhada_nao_altera_a_ou_b(self):
        at=interface()
        antes=deepcopy(at.session_state["m02_a_individual"])
        for pergunta,_ in FAQ:
            self.assertFalse(por_rotulo(at.expander,pergunta).proto.expanded)
        at.run()
        self.assertEqual(at.session_state["m02_a_individual"],antes)
        at.segmented_control[0].set_value("Experimento B").run()
        antes_b=deepcopy(at.session_state["m02_b_estado"])
        for pergunta,_ in FAQ:
            self.assertFalse(por_rotulo(at.expander,pergunta).proto.expanded)
        at.run()
        self.assertEqual(at.session_state["m02_b_estado"],antes_b)
        self.assertEqual(at.session_state["m02_a_individual"],antes)
        self.assertFalse(at.exception)

    def test_nomes_acessiveis_conservam_valores_internos_e_decomposicao(self):
        at=interface();at.segmented_control[0].set_value("Experimento B").run()
        por_rotulo(at.radio,"Modo do Experimento B").set_value(MODOS[2]).run()
        regiao=por_rotulo(at.radio,"Região principal")
        self.assertEqual(regiao.options,[REGIOES[k] for k in ("EC","EP","DWL")])
        por_rotulo(at.radio,"Regime para a região").set_value("Monopólio").run()
        self.assertEqual(at.metric[0].value,"355,56")
        self.assertEqual(at.metric[0].label,"Excedente do consumidor (EC) · u.m.")
        por_rotulo(at.checkbox,"Examinar origem da perda de eficiência").check().run()
        self.assertEqual(por_rotulo(at.radio,"Região da decomposição").options,
                         [REGIOES[k] for k in ("DWL","T","L_C","L_P")])
        for area,valor in (("T","355,56"),("L_C","88,89"),("L_P","88,89")):
            por_rotulo(at.radio,"Região da decomposição").set_value(area).run()
            self.assertEqual(at.session_state["m02_b_estado"].parcela,area)
            self.assertEqual(at.metric[0].label,REGIOES[area]+" · u.m.")
            self.assertEqual(at.metric[0].value,valor)
        por_rotulo(at.checkbox,"Examinar origem da perda de eficiência").uncheck().run()
        self.assertEqual(por_rotulo(at.radio,"Região principal").value,"EC")
        self.assertEqual(por_rotulo(at.radio,"Regime para a região").value,"Monopólio")
        self.assertFalse(at.exception)

    def test_navegacao_segmentada_preserva_referencia_precisao_e_b(self):
        at=interface()
        por_rotulo(at.button,"Ir para lucro máximo").click().run()
        por_rotulo(at.sidebar.button,"Fixar cenário de referência").click().run()
        antes_a=deepcopy(at.session_state["m02_a_individual"])
        at.segmented_control[0].set_value("Experimento B").run()
        por_rotulo(at.radio,"Modo do Experimento B").set_value(MODOS[1]).run()
        antes_b=deepcopy(at.session_state["m02_b_estado"])
        at.segmented_control[0].set_value("Experimento A").run()
        self.assertEqual(at.session_state["m02_a_individual"],antes_a)
        self.assertEqual(at.session_state["m02_a_individual"].escolha.q,80/3)
        self.assertEqual(por_rotulo(at.radio,"Zoom comparativo").value,"Sincronizado")
        at.segmented_control[0].set_value("Experimento B").run()
        self.assertEqual(at.session_state["m02_b_estado"],antes_b)
        self.assertEqual([m.value for m in at.metric],["60,00","46,67","46,67","73,33"])
        self.assertFalse(at.exception)


if __name__=="__main__": unittest.main(verbosity=2)
