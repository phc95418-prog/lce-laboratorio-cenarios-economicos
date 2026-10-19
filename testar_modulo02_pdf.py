"""Prova de integração com Chromium instalado; não instala nem configura programas."""
import unittest
from unittest.mock import patch
from modulo_02.exportacao_pdf import gerar_pdf,navegador_pdf

SVG='<svg xmlns="http://www.w3.org/2000/svg" width="700" height="420"><rect width="700" height="420" fill="white"/><path d="M 50 50 L 650 350" stroke="blue"/><text x="50" y="390">LCE - Quantidade (unidades)</text></svg>'

class ExportacaoPDF(unittest.TestCase):
    @unittest.skipUnless(navegador_pdf(),"Chrome/Chromium não disponível neste ambiente")
    def test_gera_pdf_real_com_estrutura_e_dimensoes(self):
        pdf=gerar_pdf(SVG)
        self.assertTrue(pdf.startswith(b"%PDF-"));self.assertIn(b"%%EOF",pdf[-1024:])
        self.assertGreater(len(pdf),1000)
        self.assertIn(b"/MediaBox",pdf)
    def test_sem_renderizador_informa_indisponibilidade(self):
        with patch("modulo_02.exportacao_pdf.navegador_pdf",return_value=None):
            with self.assertRaisesRegex(RuntimeError,"indisponível"): gerar_pdf(SVG)

if __name__=="__main__": unittest.main(verbosity=2)
