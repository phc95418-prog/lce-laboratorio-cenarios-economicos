"""Contratos de exportação; arquivos reais são verificados no navegador."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from experimentos import cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios
from modelo_mercado import simular_mercado
from visualizacoes import grafico_mercado, grafico_composicao_excedente, grafico_reparticao, grafico_distorcao
from exportacao_modulo01 import catalogo_exportacao
from interface_exportacao_modulo01 import preparar_pdf


def preparar(ambiente="Exploração livre", t=20, indice=0):
    cs = None
    if ambiente != "Exploração livre":
        cs = resultados_cenarios((cenarios_experimento_a if ambiente == "Experimento A" else cenarios_experimento_b)(t))
    nome, r = cs[indice] if cs else ("Mercado vigente", simular_mercado(100,1,20,1,t))
    fs = {"E1":grafico_mercado(r,cs), "E2":grafico_composicao_excedente(r)}
    if cs:
        fs["E3" if ambiente == "Experimento A" else "E4"] = (grafico_reparticao if ambiente == "Experimento A" else grafico_distorcao)(cs)
    return catalogo_exportacao(r,ambiente,nome,cs,fs), r, cs, fs


class Exportacao(unittest.TestCase):
    def test_alvos_disponiveis_explicitos(self):
        for ambiente, ids in (("Exploração livre",["E1","E2"]),("Experimento A",["E1","E2","E3"]),("Experimento B",["E1","E2","E4"])):
            c,_,_,_=preparar(ambiente)
            self.assertEqual([a["id"] for a in c["alvos"]],ids)
            self.assertEqual(len({a["seletor"] for a in c["alvos"]}),len(ids))

    def test_figuras_identicas_e_sem_mutacao(self):
        c,r,cs,fs=preparar("Experimento A")
        antes=deepcopy((r,cs))
        for a in c["alvos"]:
            self.assertEqual(a["figura"],json.loads(fs[a["id"]].to_json()))
        catalogo_exportacao(r,"Experimento A",cs[0][0],cs,fs)
        self.assertEqual((r,cs),antes)

    def test_zero_precos_validos_sem_carga(self):
        c,r,_,_=preparar(t=0)
        self.assertEqual((r["qt"],r["pc"],r["pp"]),(40,60,60))
        self.assertTrue(all("sem carga tributária efetiva" in a["nota"] for a in c["alvos"]))

    def test_interior_valores_completos(self):
        c,r,_,_=preparar()
        self.assertEqual((r["qt"],r["pc"],r["pp"],r["arrecadacao"],r["peso_morto"]),(30,70,50,600,100))
        self.assertIn("20/unidade",c["alvos"][0]["contexto"])

    def test_proibitivo_sem_precos_efetivos(self):
        for t in (80,90):
            c,r,_,_=preparar(t=t)
            self.assertEqual((r["qt"],r["pc"],r["pp"]),(0,None,None))
            self.assertTrue(all("Sem transações, preços negociados ou carga efetiva" in a["nota"] for a in c["alvos"]))

    def test_b40_comparacao_completa(self):
        c,_,cs,_=preparar("Experimento B",40)
        self.assertEqual([r["qt"] for _,r in cs],[0,20,24])
        barras=c["alvos"][-1]["figura"]["data"]
        self.assertEqual(list(barras[0]["y"]),[0,800,960])
        self.assertEqual(list(barras[1]["y"]),[800,400,320])
        self.assertIn("B1",c["alvos"][-1]["nota"])
        self.assertIn("Com transações: B2",c["alvos"][-1]["nota"])

    def test_destaque_nao_reduz_comparacao(self):
        a,*_=preparar("Experimento A",20,0)
        b,*_=preparar("Experimento A",20,2)
        self.assertEqual(a["alvos"][-1],b["alvos"][-1])
        self.assertNotEqual(a["alvos"][0],b["alvos"][0])

    def test_hash_invalida_dados_anteriores_sem_arredondar(self):
        a,*_=preparar(t=20)
        b,*_=preparar(t=20.00000001)
        self.assertNotEqual(a["contexto"],b["contexto"])
        self.assertEqual(a,preparar(t=20)[0])

    def test_nomes_sem_caminhos_ou_dados_locais(self):
        for ambiente in ("Exploração livre","Experimento A","Experimento B"):
            for a in preparar(ambiente)[0]["alvos"]:
                self.assertRegex(a["arquivo"],r"^lce-m01-[a-z0-9-]+$")

    def test_rejeita_catalogo_incompativel(self):
        _,r,cs,fs=preparar()
        with self.assertRaises(ValueError): catalogo_exportacao(r,"Experimento B","",cs,fs)

    def test_pdf_somente_alvo_e_contexto_vigentes(self):
        c,*_=preparar()
        a=c["alvos"][0]
        p=dict(contexto=c["contexto"],id=a["id"],arquivo=a["arquivo"],svg="svg-verificado")
        with patch("interface_exportacao_modulo01.gerar_pdf",return_value=b"%PDF-teste") as gerar:
            pronto=preparar_pdf(p,c)
            gerar.assert_called_once_with("svg-verificado")
            self.assertEqual(pronto["arquivo"],a["arquivo"]+".pdf")
            for alteracao in (dict(contexto="antigo"),dict(id="E4"),dict(arquivo="../../outro")):
                with self.assertRaises(ValueError): preparar_pdf({**p,**alteracao},c)
            self.assertEqual(gerar.call_count,1)

    def test_pdf_falha_localizada_sem_modificar_catalogo(self):
        c,*_=preparar(); antes=deepcopy(c); a=c["alvos"][0]
        with patch("interface_exportacao_modulo01.gerar_pdf",side_effect=RuntimeError("navegador indisponível")):
            with self.assertRaisesRegex(RuntimeError,"indisponível"):
                preparar_pdf(dict(contexto=c["contexto"],id=a["id"],arquivo=a["arquivo"],svg="svg"),c)
        self.assertEqual(c,antes)


if __name__=="__main__": unittest.main(verbosity=2)
