"""Aceitação da camada analítica M01 (Convergência v0.1, AC-03–05).

Execute com o Python da .venv. Não requer navegador, Streamlit ou componentes M02.
Oráculos numéricos incluem referências documentais e aritmética racional,
independentes do código de apresentação. Nenhum teste altera arquivos.
"""
import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError
from fractions import Fraction
import math
from pathlib import Path
import unittest

from analise_modulo01 import (
    DIMENSOES, analisar_exploracao, analisar_experimento_a, analisar_experimento_b,
)
from experimentos import cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios
from modelo_mercado import simular_mercado, parametros_por_elasticidades


def referencia(t=20):
    return simular_mercado(100, 1, 20, 1, t)


def conjunto(tipo, t=20):
    return resultados_cenarios((cenarios_experimento_a if tipo == "A" else cenarios_experimento_b)(t))


def texto(analise):
    return "\n".join((analise.base, analise.sintese, *analise.leitura, *analise.propriedades,
                      *(f.titulo + " " + f.expressao + " " + f.substituicao + " " + f.interpretacao
                        for f in analise.estrutura)))


class Individual(unittest.TestCase):
    def test_contrato_tres_dimensoes_e_base(self):
        self.assertEqual(DIMENSOES, ("Leitura econômica", "Estrutura matemática", "Propriedades e limites"))
        a = analisar_exploracao(referencia())
        self.assertIn("mesmas curvas", a.base)
        self.assertIn("não compara edições anteriores", a.base)
        self.assertEqual(len(a.cenarios), 1)
        self.assertTrue(a.sintese and a.leitura and a.estrutura and a.propriedades)

    def test_referencia_20_e_bem_estar(self):
        a = analisar_exploracao(referencia())
        v = dict(a.cenarios[0].valores)
        esperado = dict(q0=40, qt=30, p0=60, pc=70, pp=50, arrecadacao=600,
                        peso_morto=100, ec0=800, ep0=800, ec=450, ep=450, et=1500, et0=1600)
        for k, valor in esperado.items():
            self.assertEqual(v[k], valor, k)
        for trecho in ("40,00 → 30,00", "R$ 600,00", "R$ 100,00", "50,00%",
                       "R$ 700,00", "consumidores R$ 350,00", "produtores R$ 350,00"):
            self.assertIn(trecho, texto(a))

    def test_substituicoes_numericas_referencia(self):
        a = analisar_exploracao(referencia())
        formulas = {f.titulo: f for f in a.estrutura}
        self.assertEqual(formulas["Curvas vigentes"].substituicao,
                         r"P_D(Q)=100-(1)Q,\quad P_S(Q)=20+(1)Q")
        self.assertIn(r"\frac{100-20-20}{1+1}", formulas["Equilíbrios e quantidade"].substituicao)
        self.assertIn(r"P_C=100-(1)(30)\approx 70", formulas["Preços e repasse efetivo — 0<t<a−c"].substituicao)
        self.assertIn(r"\frac{(20)^2}{2(1+1)}\approx 100", formulas["Peso morto no interior"].substituicao)
        self.assertIn("450+450+600", formulas["Arrecadação e excedente total"].substituicao)
        self.assertIn("(800-450)+(800-450)", formulas["Perdas privadas e transferência"].substituicao)
        self.assertIn("R$ 300,00", texto(a))
        self.assertTrue(all(f.expressao and f.substituicao and f.interpretacao for f in a.estrutura))

    def test_imposto_zero_precos_validos_sem_carga(self):
        a = analisar_exploracao(referencia(0))
        v = dict(a.cenarios[0].valores)
        self.assertEqual(a.cenarios[0].regime, "sem_imposto")
        self.assertEqual((v["qt"], v["pc"], v["pp"]), (40, 60, 60))
        self.assertEqual((v["arrecadacao"], v["peso_morto"]), (0, 0))
        self.assertIsNone(v["fracao_consumidor_efetiva"])
        self.assertIn("há transações e preços válidos", texto(a))
        self.assertIn("Não há carga tributária efetiva", texto(a))
        self.assertNotIn("Preços e repasse efetivo", " ".join(f.titulo for f in a.estrutura))

    def test_proibitivo_80_reservas_nao_precos_negociados(self):
        a = analisar_exploracao(referencia(80))
        v = dict(a.cenarios[0].valores)
        self.assertEqual((v["qt"], v["arrecadacao"], v["peso_morto"]), (0, 0, 1600))
        self.assertIsNone(v["pc"])
        self.assertIsNone(v["pp"])
        self.assertIsNone(v["fracao_consumidor_efetiva"])
        self.assertIn("preços de reserva no limite, não preços transacionados", texto(a))
        self.assertFalse(any("interior" in f.titulo or "repasse efetivo" in f.titulo for f in a.estrutura))

    def test_acima_limiar_90_nao_extrapola_quadratica(self):
        a = analisar_exploracao(referencia(90))
        self.assertEqual(dict(a.cenarios[0].valores)["peso_morto"], 1600)
        self.assertNotIn(r"\frac{t^2}", " ".join(f.expressao for f in a.estrutura))
        self.assertIn("superestimaria", texto(a))
        self.assertIn("PM=ET_0=1600", " ".join(f.substituicao for f in a.estrutura))

    def test_lados_assimetricos(self):
        cenarios = conjunto("A")
        demanda = analisar_exploracao(cenarios[1][1])
        oferta = analisar_exploracao(cenarios[2][1])
        self.assertIn("em maior parcela pelos consumidores", texto(demanda))
        self.assertIn("75,00%", texto(demanda))
        self.assertIn("em maior parcela pelos produtores", texto(oferta))
        self.assertIn("25,00%", texto(oferta))

    def test_equivalencia_modos_de_entrada(self):
        convertido = parametros_por_elasticidades(60, 40, 1.5, 1.5, 20)
        self.assertEqual(analisar_exploracao(simular_mercado(**convertido)), analisar_exploracao(referencia()))

    def test_elasticidade_nao_inclinacao_e_oferta_unitaria(self):
        p = parametros_por_elasticidades(60, 40, 2, 1, 20)
        a = analisar_exploracao(simular_mercado(**p))
        self.assertEqual(dict(a.cenarios[0].valores)["elasticidade_oferta_0"], 1)
        self.assertIn("inclinação não é elasticidade constante", texto(a))
        self.assertIn("ε_S=1+c/(dQ)≥1", texto(a))
        expressao = " ".join(f.expressao for f in a.estrutura)
        self.assertIn(r"\frac{\varepsilon_{S,0}}{\varepsilon_{S,0}+|\varepsilon_{D,0}|}", expressao)

    def test_oraculo_racional_antes_da_formatacao(self):
        # Parâmetros racionais: resultado exato não depende de texto nem motor.
        a, b, c, d, t = map(Fraction, (100, 1, 20, 2, 7))
        q0 = (a-c)/(b+d)
        qt = (a-c-t)/(b+d)
        pc, pp = a-b*qt, c+d*qt
        ec, ep, receita = b*qt**2/2, d*qt**2/2, t*qt
        pm = (b+d)*(q0-qt)**2/2
        r = simular_mercado(*(float(v) for v in (a,b,c,d,t)))
        saida = analisar_exploracao(r)
        v = dict(saida.cenarios[0].valores)
        for k, esperado in dict(q0=q0, qt=qt, pc=pc, pp=pp, ec=ec, ep=ep,
                                arrecadacao=receita, peso_morto=pm).items():
            self.assertAlmostEqual(v[k], float(esperado), places=11)
        self.assertEqual(v["q0"], r["q0"])
        self.assertNotEqual(v["q0"], round(r["q0"], 2))
        self.assertIn("26{,}666666666666668", " ".join(f.substituicao for f in saida.estrutura))
        self.assertIn("24,33", saida.sintese)

    def test_parametros_fracionarios_cientificos(self):
        r = simular_mercado(1e-6, 0.125, 1e-7, 0.25, 1e-8)
        a = analisar_exploracao(r)
        self.assertEqual(dict(a.cenarios[0].valores)["t"], 1e-8)
        self.assertIn(r"\times10^{-8}", " ".join(f.substituicao for f in a.estrutura))

    def test_hipoteses_unidades_e_ep_nao_lucro(self):
        t = texto(analisar_exploracao(referencia()))
        for item in ("não equivale automaticamente ao lucro", "efeitos-renda", "mesmo peso monetário",
                     "R$/unidade", "R$/período", "não previsões empíricas", "obrigação legal"):
            self.assertIn(item, t)

    def test_sem_mutacao_e_saida_imutavel(self):
        r = referencia()
        antes = deepcopy(r)
        a = analisar_exploracao(r)
        self.assertEqual(r, antes)
        self.assertEqual(a, analisar_exploracao(r))
        r["qt"] = 99
        self.assertEqual(dict(a.cenarios[0].valores)["qt"], 30)
        with self.assertRaises(FrozenInstanceError):
            a.base = "outra"


class Comparacoes(unittest.TestCase):
    def test_a_referencia_todos_os_mercados(self):
        a = analisar_experimento_a(conjunto("A"))
        self.assertEqual(len(a.cenarios), 3)
        self.assertIn("b+d=2", a.base)
        self.assertIn("ENTRE os três cenários", texto(a))
        self.assertIn("podem mudar quando o imposto comum muda", texto(a))
        self.assertEqual([dict(c.valores)["fracao_consumidor_efetiva"] for c in a.cenarios], [.5,.75,.25])
        for c in a.cenarios:
            v = dict(c.valores)
            self.assertEqual((v["qt"],v["arrecadacao"],v["peso_morto"]), (30,600,100))
            self.assertTrue(any(f.cenario == c.nome and "repasse efetivo" in f.titulo for f in a.estrutura))

    def test_a_zero_e_proibitivo(self):
        for t, regime, qt, pm in ((0,"sem_imposto",40,0),(80,"proibitivo",0,1600)):
            with self.subTest(t=t):
                a = analisar_experimento_a(conjunto("A",t))
                self.assertEqual([c.regime for c in a.cenarios], [regime]*3)
                for c in a.cenarios:
                    v = dict(c.valores)
                    self.assertEqual((v["qt"],v["arrecadacao"],v["peso_morto"]), (qt,0,pm))
                    self.assertIsNone(v["fracao_consumidor_efetiva"])
                self.assertFalse(any("repasse efetivo" in f.titulo for f in a.estrutura))

    def test_b_referencia_e_bases_iniciais_distintas(self):
        a = analisar_experimento_b(conjunto("B"))
        self.assertIn("b=d", a.base)
        self.assertIn("não é ranking distributivo ou normativo", texto(a))
        for c, esperado in zip(a.cenarios, ((20,400,200,800),(30,600,100,1600),(32,640,80,2000))):
            v = dict(c.valores)
            self.assertEqual(tuple(v[k] for k in ("qt","arrecadacao","peso_morto","et0")), esperado)
            self.assertEqual(v["fracao_consumidor_efetiva"], .5)
            for k in ("qt","arrecadacao","peso_morto"):
                self.assertTrue(any(c.nome in linha and f'{v[k]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') in linha for linha in a.leitura))

    def test_b_40_fronteira_mista(self):
        a = analisar_experimento_b(conjunto("B",40))
        self.assertEqual([c.regime for c in a.cenarios], ["proibitivo","interior","interior"])
        v = [dict(c.valores) for c in a.cenarios]
        self.assertEqual([r["qt"] for r in v], [0,20,24])
        self.assertEqual([r["peso_morto"] for r in v], [800,400,320])
        self.assertIsNone(v[0]["pc"])
        self.assertIsNone(v[0]["fracao_consumidor_efetiva"])
        self.assertEqual([r["pc"] for r in v[1:]], [80,80])
        self.assertNotIn("Peso morto no interior", " ".join(f.titulo for f in a.estrutura if f.cenario==a.cenarios[0].nome))
        self.assertEqual(sum(f.titulo=="Peso morto no interior" for f in a.estrutura), 2)
        self.assertIn("B1 tem limiar proibitivo t=40", texto(a))

    def test_substituicoes_b_por_cenario_sem_usar_destaque(self):
        a = analisar_experimento_b(conjunto("B"))
        for c, esperado in zip(a.cenarios, (
            r"\frac{(20)^2}{2(0{,}5+0{,}5)}\approx 200",
            r"\frac{(20)^2}{2(1+1)}\approx 100",
            r"\frac{(20)^2}{2(1{,}25+1{,}25)}\approx 80",
        )):
            formula = next(f for f in a.estrutura if f.cenario==c.nome and f.titulo=="Peso morto no interior")
            self.assertIn(esperado,formula.substituicao)

    def test_transicoes_sem_textos_antigos_ou_instrucoes_dirigidas(self):
        antes = analisar_experimento_a(conjunto("A",20))
        for t in (0,80,1,60,20):
            a = analisar_experimento_a(conjunto("A",t))
            for palavra in ("aumente", "reduza", "experimente", "questão para", "procure"):
                self.assertNotIn(palavra, texto(a).lower())
        self.assertEqual(antes,a)

    def test_b_zero_todos_sem_distorcao(self):
        a = analisar_experimento_b(conjunto("B",0))
        for c in a.cenarios:
            v = dict(c.valores)
            self.assertEqual((v["qt"],v["pc"],v["pp"],v["peso_morto"]), (40,60,60,0))
            self.assertIsNone(v["fracao_consumidor_efetiva"])
        self.assertIn("não há distorção nem incidência efetiva", texto(a))

    def test_destaque_individual_nao_vira_comparacao(self):
        dados = conjunto("A")
        individual = analisar_exploracao(dados[1][1], nome=dados[1][0])
        comparativa = analisar_experimento_a(dados)
        self.assertEqual(len(individual.cenarios), 1)
        self.assertNotIn(dados[0][0], texto(individual))
        self.assertNotIn("ENTRE os três", texto(individual))
        for nome, _ in dados:
            self.assertIn(nome, texto(comparativa))

    def test_ordem_rotulos_e_determinismo_sem_mutacao(self):
        dados = conjunto("B")
        antes = deepcopy(dados)
        a = analisar_experimento_b(dados)
        self.assertEqual(a, analisar_experimento_b(dados))
        self.assertEqual(dados, antes)
        invertida = analisar_experimento_b(list(reversed(dados)))
        self.assertEqual([c.nome for c in invertida.cenarios], [n for n,_ in reversed(dados)])
        self.assertEqual(dict(invertida.cenarios[0].valores)["qt"], 32)

    def test_invariancias_a_varios_impostos_com_oraculo(self):
        for t in (0,1,20,40,60,79,80):
            with self.subTest(t=t):
                a = analisar_experimento_a(conjunto("A",t))
                qt = Fraction(80-t,2)
                pm = Fraction(t*t,4)
                for c in a.cenarios:
                    v = dict(c.valores)
                    self.assertEqual(v["qt"], float(qt))
                    self.assertEqual(v["arrecadacao"], float(t*qt))
                    self.assertEqual(v["peso_morto"], float(pm))


class ContratosInvalidos(unittest.TestCase):
    def test_resultado_ausente_incompleto_e_nao_finito(self):
        for r in (None, {}, "mercado", {**referencia(), "qt":math.nan},
                  {**referencia(), "t":math.inf}, {**referencia(), "b":True}):
            with self.subTest(r=type(r)):
                with self.assertRaises(ValueError): analisar_exploracao(r)

    def test_dominio_invalido(self):
        for k,v in (("b",0),("d",-1),("a",20),("c",-1),("t",-1),("qt",-2),("q0",0)):
            with self.subTest(k=k):
                with self.assertRaises(ValueError): analisar_exploracao({**referencia(),k:v})

    def test_precos_e_carga_nao_inventados(self):
        for r in ({**referencia(80),"pc":100}, {**referencia(0),"fracao_consumidor_efetiva":.5},
                  {**referencia(),"pp":None}, {**referencia(),"ha_transacoes":False}):
            with self.assertRaises(ValueError): analisar_exploracao(r)

    def test_comparacao_nao_aceita_subconjuntos_duplicatas_ou_mistura(self):
        dados = conjunto("A")
        for invalidos in (None, [], dados[:1], dados[:2], dados+[dados[0]],
                          [dados[0],dados[0],dados[2]], [dados[0],dados[1],conjunto("B")[0]],
                          [dados[0],dados[1],conjunto("A",30)[2]]):
            with self.subTest(tipo=type(invalidos)):
                with self.assertRaises(ValueError): analisar_experimento_a(invalidos)

    def test_comparacao_valida_presets_nao_so_nomes(self):
        dados = conjunto("A")
        dados[1] = (dados[1][0],simular_mercado(110,1,20,1,20))
        with self.assertRaises(ValueError): analisar_experimento_a(dados)
        with self.assertRaises(ValueError): analisar_experimento_a(conjunto("B"))

    def test_respeita_faixas_sem_ampliar_controles(self):
        with self.assertRaises(ValueError): analisar_experimento_a(conjunto("A",81))
        with self.assertRaises(ValueError): analisar_experimento_b(conjunto("B",41))
        self.assertEqual(analisar_exploracao(referencia(90)).cenarios[0].regime,"proibitivo")

    def test_sem_dependencias_de_interface_modulo02_ou_motor_paralelo(self):
        codigo = Path(__file__).with_name("analise_modulo01.py").read_text(encoding="utf-8")
        arvore = ast.parse(codigo)
        modulos = [no.module for no in ast.walk(arvore) if isinstance(no, ast.ImportFrom)]
        modulos += [n.name for no in ast.walk(arvore) if isinstance(no, ast.Import) for n in no.names]
        self.assertFalse(any(m and m.startswith(("streamlit","plotly","modulo_02")) for m in modulos))
        self.assertFalse(any(isinstance(no,ast.Name) and no.id=="simular_mercado" for no in ast.walk(arvore)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
