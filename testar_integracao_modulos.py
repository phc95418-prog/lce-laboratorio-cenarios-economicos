"""Roteamento e isolamento locais; execução Linux real continua pendente."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest
from modulo_02.exportacao_pdf import navegador_pdf


def iniciar(arquivo="lce_integrado.py"):
    # Cada AppTest possui um Runtime; os registros V2 precisam acompanhá-lo.
    for nome in ("interface_individual", "interface_comparacao", "interface_b", "janela_variaveis", "estrutura_visual"):
        sys.modules.pop("modulo_02."+nome, None)
    return AppTest.from_file(arquivo, default_timeout=20).run()


class Navegacao(unittest.TestCase):
    def test_inicia_so_modulo01_e_mantem_imposto_ao_retornar(self):
        at=iniciar()
        self.assertFalse(at.exception)
        self.assertEqual(at.title[0].value,"Quem realmente paga um imposto?")
        self.assertNotIn("m02_a_individual",at.session_state)
        at.number_input(key="lce_imposto_livre").set_value(13).run()
        at.switch_page("lce_modulo02.py").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.title),1)
        self.assertNotIn("Investigar",[r.label for r in at.radio])
        at.switch_page("app.py").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.number_input(key="lce_imposto_livre").value,13)
        self.assertNotIn("Experimento",[r.label for r in at.segmented_control])
        self.assertFalse(at.warning)

    def test_modulo01_experimento_paineis_e_escolhas_preservados(self):
        at=iniciar()
        at.radio(key="lce_ambiente").set_value("Experimento A").run()
        at.slider(key="lce_imposto_comum_a").set_value(7).run()
        paineis=("lce_analise_individual", "lce_analise_comparativa_a", "lce_m01_sobre_modelo")
        for chave in paineis:
            at.session_state[chave]=True
        at.session_state["lce_abas_investigacao"]="Comparar cenários"
        at.session_state["lce_analise_comparativa_a_dimensao"]="Estrutura matemática"
        at.run()
        at.switch_page("lce_modulo02.py").run()
        at.switch_page("app.py").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.radio(key="lce_ambiente").value,"Experimento A")
        self.assertEqual(at.slider(key="lce_imposto_comum_a").value,7)
        self.assertTrue(all(at.session_state[chave] for chave in paineis))
        self.assertEqual(at.session_state["lce_abas_investigacao"],"Comparar cenários")
        self.assertEqual(at.session_state["lce_analise_comparativa_a_dimensao"],"Estrutura matemática")
        self.assertFalse(any(r.key=="lce_a_questao" for r in at.radio))
        self.assertTrue(any(e.label=="Análise econômica e matemática" for e in at.expander))
        self.assertNotIn("Modelo e hipóteses",[t.label for t in at.tabs])

    def test_seletor_explicito_e_modulo_ativo(self):
        at=iniciar()
        for arquivo,ativo in (("app.py","Módulo 01"),("lce_modulo02.py","Módulo 02")):
            at.switch_page(arquivo).run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.get("page_link")),2)
            self.assertTrue(any("Em uso: "+ativo in c.value for c in at.caption))

    def test_analises_e_exportacoes_modernas_apos_retorno(self):
        at=iniciar()
        at.radio(key="lce_ambiente").set_value("Experimento B").run()
        at.slider(key="lce_imposto_comum_b").set_value(40).run()
        antes=[m.value for m in at.metric]
        at.switch_page("lce_modulo02.py").run()
        at.switch_page("app.py").run()
        self.assertFalse(at.exception)
        self.assertEqual([m.value for m in at.metric],antes)
        self.assertEqual(at.metric[3].value,"—")
        self.assertTrue(any(s.value=="Síntese econômica" for s in at.subheader))
        self.assertTrue(any(e.label=="Sobre o modelo" for e in at.expander))
        exportacao=next(json.loads(x.proto.json) for x in at.get("bidi_component") if x.proto.json and '"alvos"' in x.proto.json)
        self.assertEqual([a["id"] for a in exportacao["alvos"]],["E1","E2","E4"])

    def test_nova_sessao_nao_herda_mercados(self):
        a=iniciar().switch_page("lce_modulo02.py").run()
        from modulo_02.estado_individual import aplicar_evento
        aplicar_evento(a.session_state["m02_a_individual"],"q",dict(seq=1,fase="campo",texto="31"))
        a.run()
        b=iniciar().switch_page("lce_modulo02.py").run()
        self.assertFalse(b.exception)
        self.assertEqual(b.session_state["m02_a_individual"].escolha.q,25)

    def test_troca_experimentos_m01_respeita_novo_limite_de_imposto(self):
        at=iniciar()
        at.radio(key="lce_ambiente").set_value("Experimento A").run()
        at.slider(key="lce_imposto_comum_a").set_value(80).run()
        at.radio(key="lce_ambiente").set_value("Experimento B").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.slider(key="lce_imposto_comum_b").value,20)

    def test_a_comparacao_b_e_quantidades_sobrevivem_troca_modulo(self):
        from modulo_02.estado_individual import aplicar_evento
        at=iniciar().switch_page("lce_modulo02.py").run()
        aplicar_evento(at.session_state["m02_a_individual"],"q",dict(seq=1,fase="campo",texto="26,67"))
        at.run()
        next(b for b in at.sidebar.button if b.label=="Fixar cenário de referência").click().run()
        antes=deepcopy(at.session_state["m02_a_individual"])
        at.segmented_control[0].set_value("Experimento B").run()
        at.radio(key="m02_b_modo").set_value("Investigar o bem-estar").run()
        antes_b=deepcopy(at.session_state["m02_b_estado"])
        at.switch_page("app.py").run()
        at.switch_page("lce_modulo02.py").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.segmented_control[0].value,"Experimento B")
        self.assertEqual(at.session_state["m02_b_estado"],antes_b)
        at.segmented_control[0].set_value("Experimento A").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m02_a_individual"],antes)

    def test_integrador_nao_altera_configuracao_global_toolbar(self):
        with patch.object(st,"set_option",wraps=st.set_option) as opcao:
            at=iniciar().switch_page("lce_modulo02.py").run()
            at.switch_page("app.py").run()
            self.assertFalse(at.exception)
            opcao.assert_not_called()

    def test_entrypoints_individuais_continuam_operacionais(self):
        for arquivo,titulo in (("app.py","Quem realmente paga um imposto?"),
                               ("lce_modulo02.py","Módulo 02 · Decisões da Firma")):
            with self.subTest(arquivo=arquivo):
                at=iniciar(arquivo)
                self.assertFalse(at.exception)
                self.assertEqual(at.title[0].value,titulo)
                self.assertNotIn("_lce_integrado",at.session_state)

    def test_sem_navegador_aplicacao_e_png_svg_continuam(self):
        with patch("modulo_02.exportacao_pdf.navegador_pdf",return_value=None):
            at=iniciar().switch_page("lce_modulo02.py").run()
            self.assertFalse(at.exception)
            self.assertEqual(at.metric[0].value,"25,00")
            dados=[json.loads(x.proto.json) for x in at.get("bidi_component") if x.proto.json]
            configuracao=next(d for d in dados if "pdf_disponivel" in d)
            self.assertFalse(configuracao["pdf_disponivel"])


class Provisionamento(unittest.TestCase):
    def test_chromium_declarado(self):
        self.assertEqual(Path("packages.txt").read_text(encoding="utf-8").splitlines(),["chromium"])

    def test_busca_linux_aceita_usr_bin_chromium(self):
        navegador_pdf.cache_clear()
        try:
            with patch("modulo_02.exportacao_pdf.shutil.which",side_effect=lambda n:"/usr/bin/chromium" if n=="chromium" else None), \
                 patch("modulo_02.exportacao_pdf.Path.is_file",return_value=True):
                self.assertEqual(navegador_pdf(),"/usr/bin/chromium")
        finally: navegador_pdf.cache_clear()


if __name__=="__main__": unittest.main(verbosity=2)
