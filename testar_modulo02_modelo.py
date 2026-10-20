"""Aceite matemático M02 v0.4; executar com .venv/Scripts/python.exe.

Referências C1–C4 usam constantes racionais independentes. C5 cobre somente
o contrato matemático de domínio; transições reais da interface são futuras.
Integrais polinomiais e diferenças finitas verificam o motor por outra via.
Sem bibliotecas adicionais e sem reutilizar o helper de aceite no oráculo.
"""

from dataclasses import FrozenInstanceError, fields
from fractions import Fraction as F
from itertools import product
import math
import random
import unittest

from modulo_02 import (
    ParametrosFirma, ParametrosMercado, atende_aceite_analitico,
    avaliar_curvas, avaliar_firma, avaliar_mercados, calcular_otimos,
    calcular_variacao, classificar_quantidade, limitar_quantidade,
    quantidade_equivalente, validar_quantidade,
)


class Aceite(unittest.TestCase):
    def assertAnalitico(self, calculado, esperado):
        esperado = float(esperado)
        self.assertTrue(math.isfinite(calculado))
        self.assertLessEqual(
            abs(calculado - esperado), 1e-9 + 1e-9 * abs(esperado),
            f"calculado={calculado!r}; esperado={esperado!r}",
        )


class ReferenciasFirma(Aceite):
    def test_c1_otimos_exatos(self):
        otimos = calcular_otimos(ParametrosFirma())
        self.assertEqual(otimos.q_receita, 50)
        self.assertEqual(otimos.q_lucro, 80 / 3)
        self.assertEqual(otimos.tipo_lucro, "interior")

    def test_c1_firma_no_otimo(self):
        r = avaliar_firma(80 / 3, ParametrosFirma())
        self.assertAnalitico(r.curvas.receita_total, F(17600, 9))
        self.assertAnalitico(r.curvas.custo_variavel, F(8000, 9))
        self.assertAnalitico(r.lucro, F(3200, 3))
        self.assertAnalitico(r.curvas.receita_marginal, F(140, 3))
        self.assertAnalitico(r.curvas.custo_marginal, F(140, 3))
        self.assertEqual(r.classificacao, "otima")

    def test_c2_cf_zero_e_400(self):
        for cf, ct, lucro in ((0, F(1625, 2), F(2125, 2)), (400, F(2425, 2), F(1325, 2))):
            with self.subTest(cf=cf):
                r = avaliar_firma(25, ParametrosFirma(cf=cf))
                self.assertEqual(r.curvas.receita_total, 1875)
                self.assertEqual(r.custo_total, ct)
                self.assertEqual(r.lucro, lucro)

    def test_c2_cf_nao_muda_curvas_e_otimos(self):
        r0 = avaliar_firma(25, ParametrosFirma())
        r1 = avaliar_firma(25, ParametrosFirma(cf=400))
        self.assertEqual(r0.curvas, r1.curvas)
        self.assertEqual(r0.otimos, r1.otimos)
        self.assertEqual(r1.custo_total - r0.custo_total, 400)
        self.assertEqual(r1.lucro - r0.lucro, -400)

    def test_c2_lucro_maximo_negativo_sem_fechamento(self):
        r = avaliar_firma(80 / 3, ParametrosFirma(cf=1600))
        self.assertEqual(r.curvas.q, 80 / 3)
        self.assertEqual(r.otimos.q_lucro, 80 / 3)
        self.assertAnalitico(r.lucro, F(-1600, 3))

    def test_q_zero_intercepto_nao_e_preco_transacionado(self):
        r = avaliar_firma(0, ParametrosFirma(cf=400))
        self.assertEqual(r.curvas.preco_demanda, 100)
        self.assertIsNone(r.preco_transacao)
        self.assertEqual(r.curvas.receita_total, 0)
        self.assertEqual(r.custo_total, 400)
        self.assertEqual(r.lucro, -400)

    def test_c3_fronteira_igualdade(self):
        r = avaliar_firma(0, ParametrosFirma(c=100))
        self.assertEqual(r.otimos.q_lucro, 0)
        self.assertEqual(r.otimos.tipo_lucro, "fronteira_igualdade")
        self.assertEqual(r.curvas.receita_marginal, 100)
        self.assertEqual(r.curvas.custo_marginal, 100)
        self.assertEqual(r.classificacao, "otima")

    def test_c3_fronteira_sem_intersecao(self):
        r = avaliar_firma(0, ParametrosFirma(c=120))
        self.assertEqual(r.otimos.tipo_lucro, "fronteira_sem_intersecao")
        self.assertEqual(r.otimos.q_lucro, 0)
        self.assertEqual(r.curvas.receita_marginal, 100)
        self.assertEqual(r.curvas.custo_marginal, 120)

    def test_c3_producao_hipotetica_positiva_admissivel(self):
        for c in (100, 120):
            with self.subTest(c=c):
                r = avaliar_firma(25, ParametrosFirma(c=c))
                self.assertEqual(r.curvas.q, 25)
                self.assertEqual(r.classificacao, "acima")
                self.assertLess(r.lucro, 0)
                self.assertEqual(r.preco_transacao, 75)

    def test_rmg_negativa_e_extremo_do_dominio(self):
        r = avaliar_firma(100, ParametrosFirma())
        self.assertEqual(r.curvas.receita_marginal, -100)
        self.assertEqual(r.curvas.preco_demanda, 0)
        self.assertEqual(r.curvas.receita_total, 0)
        self.assertEqual(r.classificacao, "acima")

    def test_ep_nao_confundido_com_lucro(self):
        r = avaliar_firma(25, ParametrosFirma(cf=400))
        self.assertEqual(r.curvas.excedente_produtor, 1062.5)
        self.assertEqual(r.lucro, 662.5)
        self.assertAnalitico(r.lucro, r.curvas.excedente_produtor - 400)


class ReferenciasMercados(Aceite):
    def test_c1_quantidades_precos(self):
        r = avaliar_mercados(ParametrosMercado())
        self.assertEqual(r.concorrencia.curvas.q, 40)
        self.assertEqual(r.monopolio.curvas.q, 80 / 3)
        self.assertEqual(r.concorrencia.preco_transacao, 60)
        self.assertAnalitico(r.monopolio.preco_transacao, F(220, 3))

    def test_c1_excedentes_concorrencia(self):
        c = avaliar_mercados(ParametrosMercado()).concorrencia.curvas
        self.assertEqual((c.excedente_consumidor, c.excedente_produtor, c.excedente_total), (800, 800, 1600))

    def test_c1_excedentes_monopolio(self):
        m = avaliar_mercados(ParametrosMercado()).monopolio.curvas
        self.assertAnalitico(m.excedente_consumidor, F(3200, 9))
        self.assertAnalitico(m.excedente_produtor, F(3200, 3))
        self.assertAnalitico(m.excedente_total, F(12800, 9))

    def test_c1_decomposicao(self):
        d = avaliar_mercados(ParametrosMercado()).decomposicao
        for valor, esperado in (
            (d.reducao_quantidade, F(40, 3)), (d.transferencia, F(3200, 9)),
            (d.perda_consumidor, F(800, 9)), (d.perda_produtor, F(800, 9)),
            (d.peso_morto, F(1600, 9)),
        ):
            self.assertAnalitico(valor, esperado)

    def test_c1_diferencas_e_percentuais(self):
        d = avaliar_mercados(ParametrosMercado()).diferencas
        for delta, esperado in (
            (d.quantidade.absoluta, F(-40, 3)), (d.quantidade.percentual, F(-100, 3)),
            (d.preco.absoluta, F(40, 3)), (d.preco.percentual, F(200, 9)),
            (d.excedente_consumidor.absoluta, F(-4000, 9)),
            (d.excedente_produtor.absoluta, F(800, 3)),
            (d.excedente_total.absoluta, F(-1600, 9)),
        ):
            self.assertAnalitico(delta, esperado)

    def test_c3_sem_comercio_e_sem_valores_artificiais(self):
        for custo, tipo in ((100, "fronteira_igualdade"), (120, "fronteira_sem_intersecao")):
            with self.subTest(c=custo):
                r = avaliar_mercados(ParametrosMercado(c=custo))
                self.assertEqual(r.tipo_otimo_monopolio, tipo)
                for regime in (r.concorrencia, r.monopolio):
                    self.assertEqual(regime.curvas.q, 0)
                    self.assertIsNone(regime.preco_transacao)
                    self.assertEqual(regime.curvas.preco_demanda, 100)
                    for nome in ("excedente_consumidor", "excedente_produtor", "excedente_total"):
                        self.assertEqual(getattr(regime.curvas, nome), 0)
                for campo in fields(r.decomposicao):
                    self.assertEqual(getattr(r.decomposicao, campo.name), 0)
                for campo in fields(r.diferencas):
                    v = getattr(r.diferencas, campo.name)
                    self.assertIsNone(v.percentual)
                    self.assertEqual(v.absoluta, None if campo.name == "preco" else 0)

    def test_c4_referencias_racionais_sem_arredondar(self):
        r = avaliar_mercados(ParametrosMercado(b=2, s=0.25))
        # Valores derivados à mão com denominador comum 153.
        # QC=320/9; QM=320/17; dQ=2560/153.
        self.assertAnalitico(r.concorrencia.curvas.q, F(320, 9))
        self.assertAnalitico(r.monopolio.curvas.q, F(320, 17))
        self.assertAnalitico(r.decomposicao.transferencia, F(1638400, 2601))
        self.assertAnalitico(r.decomposicao.perda_consumidor, F(6553600, 23409))
        self.assertAnalitico(r.decomposicao.perda_produtor, F(819200, 23409))
        self.assertAnalitico(r.decomposicao.peso_morto, F(7372800, 23409))
        self.assertNotEqual(r.decomposicao.perda_consumidor, r.decomposicao.perda_produtor)

    def test_b_exclui_cf_e_importacao_e_copia(self):
        with self.assertRaises(TypeError):
            ParametrosMercado(cf=400)
        with self.assertRaises(TypeError):
            avaliar_mercados(ParametrosFirma(cf=400))
        resultados = []
        for cf in (0, 400, 1600):
            a = ParametrosFirma(cf=cf)
            resultados.append(avaliar_mercados(ParametrosMercado(a.a, a.b, a.c, a.s)))
        self.assertEqual(resultados[0], resultados[1])
        self.assertEqual(resultados[0], resultados[2])


class PrecisaoEClassificacao(Aceite):
    def test_80_tercos_preservado_e_distinto_de_26_67(self):
        exato = avaliar_firma(80 / 3, ParametrosFirma())
        manual = avaliar_firma(26.67, ParametrosFirma())
        self.assertEqual(exato.curvas.q, 80 / 3)
        self.assertNotEqual(exato.curvas.q, manual.curvas.q)
        self.assertEqual(exato.classificacao, "otima")
        self.assertEqual(manual.classificacao, "muito_proxima")
        self.assertAnalitico(manual.diferenca_marginal, -0.01)
        self.assertLess(manual.diferenca_marginal, 0)

    def test_igualdade_computacional_limites(self):
        self.assertTrue(quantidade_equivalente(25 + 1e-11, 25))
        self.assertFalse(quantidade_equivalente(25 + 1e-10, 25))
        self.assertTrue(quantidade_equivalente(0, 0))
        self.assertFalse(quantidade_equivalente(0, 1e-20))
        self.assertFalse(quantidade_equivalente(1e-20, 0))

    def test_positivo_minimo_nao_e_fronteira_zero(self):
        p = ParametrosFirma(c=math.nextafter(100, 0))
        r = avaliar_firma(0, p)
        self.assertGreater(r.otimos.q_lucro, 0)
        self.assertEqual(r.otimos.tipo_lucro, "interior")
        self.assertEqual(r.classificacao, "abaixo")
        b = avaliar_mercados(ParametrosMercado(c=p.c))
        self.assertGreater(b.monopolio.curvas.q, 0)
        self.assertIsNotNone(b.monopolio.preco_transacao)

    def test_proximidade_um_porcento_sem_igualdade(self):
        for q in (24.75, 25.25):
            self.assertEqual(classificar_quantidade(q, 25), "muito_proxima")
        self.assertEqual(classificar_quantidade(24.74, 25), "abaixo")
        self.assertEqual(classificar_quantidade(25.26, 25), "acima")
        self.assertEqual(classificar_quantidade(0, 0), "otima")
        self.assertEqual(classificar_quantidade(1e-20, 0), "acima")

    def test_aceite_analitico_usa_soma_das_tolerancias(self):
        self.assertTrue(atende_aceite_analitico(1 + 1.5e-9, 1))
        self.assertFalse(atende_aceite_analitico(1 + 3e-9, 1))
        self.assertTrue(atende_aceite_analitico(0.5e-9, 0))
        self.assertFalse(quantidade_equivalente(1 + 1.5e-9, 1))
        self.assertEqual(classificar_quantidade(1 + 1.5e-9, 1), "muito_proxima")

    def test_entre_ticks_e_precisao_de_entrada(self):
        p = ParametrosFirma(a=101.2345, b=1.1537, c=20.1234, s=0.7312, cf=23.4567)
        r = avaliar_firma(25.123456789, p)
        self.assertEqual(p.b, 1.1537)
        self.assertEqual(p.cf, 23.4567)
        self.assertEqual(r.curvas.q, 25.123456789)
        # Oráculo racional para o ótimo desse conjunto de decimais.
        self.assertAnalitico(r.otimos.q_lucro, F(811111, 10000) / F(30386, 10000))

    def test_variacao_base_zero_indefinida_e_negativa(self):
        self.assertEqual(calcular_variacao(10, 0, "u.m.").absoluta, 10)
        self.assertIsNone(calcular_variacao(10, 0, "u.m.").percentual)
        self.assertIsNone(calcular_variacao(None, 10, "u.m.").absoluta)
        self.assertIsNone(calcular_variacao(10, None, "u.m.").percentual)
        self.assertEqual(calcular_variacao(-50, -100, "u.m.").percentual, -50)
        self.assertEqual(calcular_variacao(125, 100, "u.m.").percentual, 25)


class DominiosEContratos(Aceite):
    def test_extremos_inclusivos_parametros(self):
        for a, b, c, s, cf in product((60, 140), (0.5, 2), (0, 160), (0.25, 3), (0, 1600)):
            p = ParametrosFirma(a, b, c, s, cf)
            for q in (0, p.q_max):
                self.assertTrue(math.isfinite(avaliar_firma(q, p).lucro))

    def test_parametros_fora_das_faixas_rejeitados(self):
        for nome, valores in {"a": (59.99, 140.01), "b": (0, 0.4999, 2.001), "c": (-0.01, 160.01), "s": (0, 0.2499, 3.001), "cf": (-1, 1600.01)}.items():
            for valor in valores:
                with self.subTest(nome=nome, valor=valor), self.assertRaises(ValueError):
                    ParametrosFirma(**{nome: valor})

    def test_parametros_invalidos_nao_finitos_e_tipos(self):
        for nome in ("a", "b", "c", "s", "cf"):
            for valor in (float("nan"), float("inf"), -float("inf"), True, None, "1", complex(1, 1), 10**400):
                with self.subTest(nome=nome, valor=repr(valor)), self.assertRaises(ValueError):
                    ParametrosFirma(**{nome: valor})

    def test_quantidades_invalidas_nao_sofrem_clamp_silencioso(self):
        for q in (-1, 100.0001, float("nan"), float("inf"), True, "25", None):
            with self.subTest(q=q), self.assertRaises(ValueError):
                avaliar_firma(q, ParametrosFirma())
        self.assertEqual(validar_quantidade(F(80, 3), ParametrosFirma()), 80 / 3)

    def test_c5_clamp_explicito_sem_restaurar_valor_anterior(self):
        origem = ParametrosFirma()
        reduzido = ParametrosFirma(a=60, b=2)
        q = limitar_quantidade(80, reduzido)
        self.assertEqual(q, 30)
        self.assertEqual(limitar_quantidade(q, origem), 30)
        self.assertEqual(limitar_quantidade(20, reduzido), 20)
        with self.assertRaises(ValueError):
            limitar_quantidade(-1, reduzido)

    def test_classes_e_aceite_rejeitam_entradas_invalidas(self):
        for q in (float("nan"), float("inf"), True, "25", -1):
            for funcao in (quantidade_equivalente, classificar_quantidade):
                with self.subTest(funcao=funcao.__name__, q=q), self.assertRaises(ValueError):
                    funcao(q, 25)
                with self.assertRaises(ValueError):
                    funcao(25, q)
        for funcao in (atende_aceite_analitico,):
            with self.assertRaises(ValueError):
                funcao(float("nan"), 1)
        with self.assertRaises(TypeError):
            avaliar_firma(25, ParametrosMercado())
        with self.assertRaises(TypeError):
            avaliar_curvas(25, {"a": 100})

    def test_resultados_e_parametros_imutaveis(self):
        p = ParametrosFirma()
        r = avaliar_firma(25, p)
        for objeto, atributo in ((p, "a"), (r, "lucro"), (r.curvas, "q")):
            with self.assertRaises(FrozenInstanceError):
                setattr(objeto, atributo, 0)

    def test_unidades_explicitas_e_sem_moeda_real(self):
        a = avaliar_firma(25, ParametrosFirma())
        b = avaliar_mercados(ParametrosMercado())
        for objeto in (a.curvas, a.otimos, a, b.concorrencia, b.decomposicao):
            for campo in fields(objeto):
                valor = getattr(objeto, campo.name)
                if isinstance(valor, float) or valor is None:
                    self.assertIn(campo.metadata["unidade"], ("unidades", "u.m./unidade", "u.m."))
        for nome, unidade in (("quantidade", "unidades"), ("preco", "u.m./unidade"), ("excedente_total", "u.m.")):
            v = getattr(b.diferencas, nome)
            self.assertEqual(v.unidade_absoluta, unidade)
            self.assertEqual(fields(v)[1].metadata["unidade"], "%")


class VerificacoesIndependentes(Aceite):
    def test_derivadas_por_diferencas_finitas(self):
        # Diferença central é exata para quadráticas, salvo erro binário.
        p = ParametrosFirma(a=123, b=1.25, c=37, s=0.75, cf=310)
        h = 0.125
        for q in (1, 15, 40, 75):
            esquerda = avaliar_firma(q - h, p)
            direita = avaliar_firma(q + h, p)
            centro = avaliar_firma(q, p)
            self.assertAnalitico((direita.curvas.receita_total - esquerda.curvas.receita_total) / (2*h), centro.curvas.receita_marginal)
            self.assertAnalitico((direita.custo_total - esquerda.custo_total) / (2*h), centro.curvas.custo_marginal)
            self.assertAnalitico((direita.lucro - esquerda.lucro) / (2*h), centro.diferenca_marginal)

    def test_otimos_sao_maximos_globais_no_dominio(self):
        for p in (ParametrosFirma(), ParametrosFirma(cf=1600), ParametrosFirma(c=100), ParametrosFirma(c=120), ParametrosFirma(a=140, b=0.5, c=0, s=0.25)):
            o = calcular_otimos(p)
            max_lucro = avaliar_firma(o.q_lucro, p).lucro
            max_receita = avaliar_curvas(o.q_receita, p).receita_total
            for i in range(101):
                r = avaliar_firma(p.q_max * i / 100, p)
                self.assertLessEqual(r.lucro, max_lucro + 1e-9)
                self.assertLessEqual(r.curvas.receita_total, max_receita + 1e-9)

    def test_identidades_e_integracao_em_200_cenarios(self):
        rng = random.Random(20261014)
        for indice in range(200):
            p = ParametrosMercado(rng.uniform(60, 140), rng.uniform(0.5, 2), rng.uniform(0, 160), rng.uniform(0.25, 3))
            with self.subTest(indice=indice):
                r = avaliar_mercados(p)
                c, m, d = r.concorrencia.curvas, r.monopolio.curvas, r.decomposicao
                self.assertAnalitico(d.peso_morto, c.excedente_total - m.excedente_total)
                self.assertAnalitico(r.diferencas.excedente_consumidor.absoluta, -d.transferencia-d.perda_consumidor)
                self.assertAnalitico(r.diferencas.excedente_produtor.absoluta, d.transferencia-d.perda_produtor)
                self.assertAnalitico(r.diferencas.excedente_total.absoluta, -d.peso_morto)
                # Integração por trapézio: exata para demanda e CMg lineares.
                for curva in (c, m):
                    q, preco = curva.q, curva.preco_demanda
                    ec_integral = ((p.a-preco) + (p.a-p.b*q-preco)) * q/2
                    ep_integral = ((preco-p.c) + (preco-p.c-p.s*q)) * q/2
                    self.assertAnalitico(curva.excedente_consumidor, ec_integral)
                    self.assertAnalitico(curva.excedente_produtor, ep_integral)
                gap_m = (p.a-p.b*m.q)-(p.c+p.s*m.q)
                gap_c = (p.a-p.b*c.q)-(p.c+p.s*c.q)
                self.assertAnalitico(d.peso_morto, (gap_m+gap_c)*(c.q-m.q)/2)
                if p.a > p.c:
                    self.assertGreater(c.q, m.q)
                    self.assertGreater(r.monopolio.preco_transacao, r.concorrencia.preco_transacao)
                    self.assertAnalitico(c.preco_demanda, c.custo_marginal)
                    self.assertAnalitico(m.receita_marginal, m.custo_marginal)
                    self.assertAnalitico(d.transferencia, (m.preco_demanda-c.preco_demanda)*m.q)


if __name__ == "__main__":
    unittest.main(verbosity=2)
