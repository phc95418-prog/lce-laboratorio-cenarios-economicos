"""Regressão focalizada dos três achados da auditoria, sem alterar arquivos."""
from dataclasses import replace
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest
from analise_modulo01 import analisar_experimento_a, analisar_experimento_b
from experimentos import cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios
from interface_analise_modulo01 import _organizar_comparacao, _substituicoes_numeradas
from recursos_modulo01 import perguntas_frequentes


def analise(tipo, t):
    return (analisar_experimento_a if tipo == "A" else analisar_experimento_b)(
        resultados_cenarios((cenarios_experimento_a if tipo == "A" else cenarios_experimento_b)(t)))


class CorrecoesAceitacao(unittest.TestCase):
    def test_retencao_integral_de_formulas_substituicoes_e_interpretacoes(self):
        for tipo, t in (("A",0),("A",20),("A",80),("B",0),("B",20),("B",40)):
            a=analise(tipo,t); relacoes, mercados=_organizar_comparacao(a)
            originais={(f.cenario,f.titulo):f for f in a.estrutura}
            mantidas={(f.cenario,f.titulo):f for fs in mercados.values() for _,f in fs}
            self.assertEqual(mantidas,originais)
            for nome, fs in mercados.items():
                latex=_substituicoes_numeradas(fs)
                for numero,f in fs:
                    for parte in f.substituicao.split(r"\quad"):
                        self.assertIn(parte.strip().rstrip(","),latex)
                    self.assertIn(nome,relacoes[(f.titulo,f.expressao,f.interpretacao)][1])

    def test_a20_relacoes_comuns_uma_vez_e_tres_mercados(self):
        a=analise("A",20); rs,ms=_organizar_comparacao(a)
        self.assertEqual(len(rs),10)
        self.assertEqual(len(ms),3)
        self.assertTrue(all(len(nomes)==3 for _,nomes in rs.values()))
        for fracao,fs in zip((r"0{,}5",r"0{,}75",r"0{,}25"),ms.values()):
            self.assertIn(fracao,next(f.substituicao for _,f in fs if f.titulo.startswith("Elasticidades")))
        self.assertIn("invariâncias",a.propriedades[0])

    def test_b20_todos_interiores_sem_confundir_bases(self):
        a=analise("B",20); rs,ms=_organizar_comparacao(a)
        self.assertEqual([c.regime for c in a.cenarios],["interior"]*3)
        self.assertEqual(len(rs),10)
        self.assertEqual(len(ms),3)
        self.assertTrue(all(len(nomes)==3 for _,nomes in rs.values()))
        self.assertIn("B1",a.propriedades[0])

    def test_b40_separa_fronteira_de_formulas_interiores(self):
        a=analise("B",40); rs,ms=_organizar_comparacao(a)
        self.assertEqual([c.regime for c in a.cenarios],["proibitivo","interior","interior"])
        for (titulo,_,_),(_,nomes) in rs.items():
            if titulo=="Encerramento das transações": self.assertEqual(nomes,[a.cenarios[0].nome])
            if titulo.startswith("Preços e repasse") or titulo=="Peso morto no interior":
                self.assertEqual(nomes,[c.nome for c in a.cenarios[1:]])
        b1=_substituicoes_numeradas(ms[a.cenarios[0].nome])
        self.assertIn("PM=ET_0=800",b1)
        self.assertNotIn("P_C=",b1)
        for c,quantidade,receita,perda in zip(a.cenarios,(0,20,24),(0,800,960),(800,400,320)):
            valores=dict(c.valores)
            self.assertEqual((valores["qt"],valores["arrecadacao"],valores["peso_morto"]),(quantidade,receita,perda))

    def test_a_zero_e_proibitivo_nao_recebem_formulas_interiores(self):
        for t,regime in ((0,"sem_imposto"),(80,"proibitivo")):
            a=analise("A",t); rs,_=_organizar_comparacao(a)
            self.assertEqual([c.regime for c in a.cenarios],[regime]*3)
            self.assertFalse(any(titulo.startswith("Preços e repasse") or titulo=="Peso morto no interior" for titulo,_,_ in rs))

    def test_interpretacoes_diferentes_nao_sao_fundidas(self):
        a=analise("A",20)
        alterada=replace(a.estrutura[0],interpretacao="Condição específica de validade.")
        outra=replace(a,estrutura=(alterada,*a.estrutura[1:]))
        self.assertEqual(len(_organizar_comparacao(outra)[0]),11)

    def test_renderizacao_real_grupos_e_estados_preservados(self):
        at=AppTest.from_file(str(Path(__file__).with_name("app.py")),default_timeout=20).run()
        for tipo,t in (("A",20),("A",80),("B",20),("B",40)):
            at.radio(key="lce_ambiente").set_value("Experimento "+tipo).run()
            at.slider(key="lce_imposto_comum_"+tipo.lower()).set_value(t).run()
            self.assertFalse(at.exception)
            antes=[m.value for m in at.metric]
            comp=next(tab for tab in at.tabs if tab.label=="Comparar cenários")
            matematica=next(tab for tab in comp.tabs if tab.label=="Estrutura matemática")
            a=analise(tipo,t); rs,ms=_organizar_comparacao(a)
            self.assertEqual(len(matematica.latex),len(rs)+len(ms))
            self.assertEqual([f.value.removeprefix("$$\n").removesuffix("\n$$") for f in matematica.latex[-3:]],[_substituicoes_numeradas(fs) for fs in ms.values()])
            self.assertTrue(any(s.value=="Substituições por mercado" for s in matematica.subheader))
            unidades=next(c.value for c in matematica.caption if c.value.startswith("Os números entre colchetes"))
            self.assertEqual(unidades.count(r"R\$"),2)
            at.run()
            self.assertEqual([m.value for m in at.metric],antes)
            self.assertEqual(at.slider[0].value,t)

    def test_ajuda_exportacao_tem_local_alvo_formatos_e_contexto(self):
        for ambiente in ("Exploração livre","Experimento A","Experimento B"):
            resposta=dict(perguntas_frequentes(ambiente))["Como exportar um gráfico?"]
            for termo in ("engrenagem","selecione o gráfico","PNG","SVG","PDF","cenário vigente","Baixar PDF preparado"):
                self.assertIn(termo,resposta)


if __name__=="__main__": unittest.main(verbosity=2)
