"""Ensaios locais da integração dos três módulos; não alteram a publicação."""

from decimal import Decimal
import sys
import unittest

from streamlit.testing.v1 import AppTest
import streamlit as st


M03 = "lce_modulo03.py"
EB = "Experimento B · Mudanças na escolha ótima"


def iniciar():
    # Cada AppTest abre um Runtime distinto. Registros V2 pertencem ao Runtime.
    st.cache_resource.clear()
    for name in (
        "modulo_02.interface_individual", "modulo_02.interface_comparacao",
        "modulo_02.interface_b", "modulo_02.janela_variaveis",
        "modulo_02.estrutura_visual", "modulo_03.interface_livre",
        "modulo_03.interface_individual", "modulo_03.interface_comparacao_consumidores",
        "modulo_03.interface_experimento_b",
    ):
        sys.modules.pop(name, None)
    return AppTest.from_file("lce_integrado.py", default_timeout=25).run()


class PreIntegracao(unittest.TestCase):
    def test_somente_modulo_ativo_renderizado(self):
        at = iniciar()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.get("page_link")), 3)
        self.assertNotIn("m03_livre_value_R", at.session_state)
        self.assertNotIn("m02_a_individual", at.session_state)
        at.switch_page(M03).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m03_livre_value_R"], "120")
        self.assertNotIn("m02_a_individual", at.session_state)
        at.switch_page("lce_modulo02.py").run()
        self.assertFalse(at.exception)
        self.assertIn("m02_a_individual", at.session_state)

    def test_m01_e_m02_preservam_escolhas(self):
        at = iniciar()
        at.number_input(key="lce_imposto_livre").set_value(13).run()
        at.switch_page("lce_modulo02.py").run()
        from modulo_02.estado_individual import aplicar_evento
        aplicar_evento(at.session_state["m02_a_individual"], "q",
                      dict(seq=1, fase="campo", texto="31"))
        at.run()
        at.switch_page(M03).run()
        at.switch_page("app.py").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.number_input(key="lce_imposto_livre").value, 13)
        at.switch_page("lce_modulo02.py").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m02_a_individual"].escolha.q, 31)

    def test_m03_decimal_e_ambientes_independentes(self):
        at = iniciar().switch_page(M03).run()
        at.text_input(key="m03_livre_field_X").set_value("0.123456789012345678901").run()
        at.text_input(key="m03_livre_field_Y").set_value("2").run()
        original = at.session_state["m03_livre_manual"]
        self.assertEqual(original.x, Decimal("0.123456789012345678901"))
        self.assertTrue(any("Coordenadas confirmadas" in c.value for c in at.caption))
        at.radio(key="m03_page").set_value("Experimento A · Escolha individual").run()
        self.assertIsNone(at.session_state["m03_ai_manual"])
        at.switch_page("app.py").run().switch_page(M03).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m03_page"], "Experimento A · Escolha individual")
        at.radio(key="m03_page").set_value("Exploração livre").run()
        self.assertEqual(at.session_state["m03_livre_manual"], original)

    def test_referencia_e_hicks_apos_navegacao(self):
        at = iniciar().switch_page(M03).run()
        at.radio(key="m03_page").set_value(EB).run()
        next(b for b in at.button if b.label == "Fixar referência").click().run()
        at.text_input(key="m03_eb_field_PX").set_value("20").run()
        at.checkbox(key="m03_eb_hicks_on").set_value(True).run()
        frozen = at.session_state["m03_eb_reference"]
        self.assertEqual(frozen.solution.basket.x, Decimal(6))
        at.switch_page("lce_modulo02.py").run().switch_page("app.py").run()
        at.switch_page(M03).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m03_page"], EB)
        self.assertEqual(at.session_state["m03_eb_reference"], frozen)
        self.assertEqual(at.session_state["m03_eb_value_PX"], "20")
        self.assertTrue(at.session_state["m03_eb_hicks_on"])
        at.text_input(key="m03_eb_field_R").set_value("180").run()
        self.assertFalse(at.session_state["m03_eb_hicks_on"])
        self.assertEqual(at.session_state["m03_eb_reference"], frozen)

    def test_nova_sessao_nao_herda_referencia(self):
        a = iniciar().switch_page(M03).run()
        a.radio(key="m03_page").set_value(EB).run()
        next(b for b in a.button if b.label == "Fixar referência").click().run()
        self.assertIsNotNone(a.session_state["m03_eb_reference"])
        b = iniciar().switch_page(M03).run()
        b.radio(key="m03_page").set_value(EB).run()
        self.assertFalse(b.exception)
        self.assertIsNone(b.session_state["m03_eb_reference"])

    def test_reinicio_b_remonta_slider_alpha_sem_alterar_valor(self):
        at = iniciar().switch_page(M03).run()
        at.radio(key="m03_page").set_value(EB).run()
        at.text_input(key="m03_eb_field_A").set_value("0.000000000001").run()
        self.assertEqual(at.session_state["m03_eb_value_A"], "1E-12")
        next(b for b in at.button if b.label == "Fixar referência").click().run()
        self.assertFalse(any("Preferência" in s.label for s in at.slider))
        next(b for b in at.button if b.label == "Confirmar reinício do Experimento B").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["m03_eb_value_A"], "0.5")
        self.assertEqual(at.text_input(key="m03_eb_field_A").value, "0.5")
        self.assertEqual(next(s.value for s in at.slider if "Preferência" in s.label), 0.5)
        at.run()
        self.assertEqual(at.session_state["m03_eb_value_A"], "0.5")
        snapshot = at.session_state["_lce_paineis_modulo03"]
        self.assertFalse(any("_slider_" in k and not k.endswith("_slider_epoch")
                             for k in snapshot))
        at.switch_page("lce_modulo02.py").run().switch_page(M03).run()
        self.assertEqual(at.session_state["m03_eb_value_A"], "0.5")
        self.assertEqual(next(s.value for s in at.slider if "Preferência" in s.label), 0.5)
        exact = "0.500000000000000000001"
        at.text_input(key="m03_eb_field_A").set_value(exact).run()
        self.assertEqual(at.session_state["m03_eb_value_A"], exact)
        self.assertEqual(next(s.value for s in at.slider if "Preferência" in s.label), 0.5)
        at.run()
        self.assertEqual(at.session_state["m03_eb_value_A"], exact)


if __name__ == "__main__":
    unittest.main(verbosity=2)
