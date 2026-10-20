"""Estados, mensagens e geometria de A individual; browser é teste separado."""

from dataclasses import replace
import math
import unittest
from types import SimpleNamespace

from modulo_02 import ParametrosFirma
from modulo_02.estado_individual import (
    Escolha, EstadoIndividual, aplicar_evento, atualizar_parametros, confirmar,
    ler_numero, selecionar_otimo, selecionar_vista, revalidar_sessao,
)
from modulo_02.explicacoes_individual import (
    condicoes_excepcionais, explicacao, mensagem_marginal, mensagem_quantidade,
    numero, sintese,
)
from modulo_02.graficos_individual import grafico_individual


def evento(estado, campo, valor=None, fase="campo", texto=None):
    seq = estado.sequencias.get(campo,0)+1
    return aplicar_evento(estado,campo, {"seq":seq,"fase":fase,"texto":str(valor) if texto is None else texto,"valor":valor})


class Estados(unittest.TestCase):
    def test_inicial_ev01(self):
        e = EstadoIndividual()
        self.assertEqual(e.escolha, Escolha(ParametrosFirma(),25))
        self.assertEqual(e.perspectiva,"Resultados Totais")
        self.assertEqual(e.foco,"Geral")
        self.assertFalse(e.mostrar_otimos)
        self.assertFalse(e.interagiu)
        self.assertNotIn("26,67",sintese(e))

    def test_otimo_exato_at02(self):
        e = EstadoIndividual(); selecionar_otimo(e)
        self.assertEqual(e.escolha.q,80/3)
        self.assertEqual(e.confirmado.q,80/3)
        self.assertNotEqual(e.escolha.q,26.67)

    def test_manual_distinto_do_otimo(self):
        e = EstadoIndividual(); selecionar_otimo(e); evento(e,"q",texto="26,67")
        self.assertEqual(e.escolha.q,26.67)
        self.assertIn("muito próxima",sintese(e))

    def test_b_fora_da_grade_at15(self):
        e = EstadoIndividual(); evento(e,"b",texto="1,1537")
        self.assertEqual(e.escolha.parametros.b,1.1537)
        self.assertEqual(e.escolha.q,25)

    def test_invalidos_preservam_ultimo_calculo(self):
        e = EstadoIndividual()
        for texto in ("", "26,", "abc", "NaN", "inf", "101", "-1"):
            evento(e,"q",texto=texto)
            self.assertEqual(e.escolha.q,25)
            self.assertEqual(e.confirmado.q,25)
            self.assertIn("q",e.erros)
        evento(e,"q",texto="26,675")
        self.assertNotIn("q",e.erros)
        self.assertEqual(e.escolha.q,26.675)

    def test_arraste_preserva_base_ate_fim_ev15(self):
        e = EstadoIndividual(); evento(e,"q",30)
        antes = sintese(e)
        for q in (40,45,50):
            evento(e,"q",q,"live")
            self.assertEqual(e.escolha.q,q)
            self.assertEqual(e.confirmado.q,30)
            self.assertEqual(sintese(e),antes)
        evento(e,"q",50,"fim")
        self.assertEqual(e.anterior.q,30)
        self.assertEqual(e.confirmado.q,50)
        self.assertFalse(e.em_interacao)

    def test_clamp_e_ampliacao_v04(self):
        e = EstadoIndividual(); evento(e,"q",80)
        atualizar_parametros(e,ParametrosFirma(a=60,b=2)); confirmar(e)
        self.assertEqual(e.escolha.q,30)
        self.assertTrue(e.aviso_dominio)
        atualizar_parametros(e,ParametrosFirma()); confirmar(e)
        self.assertEqual(e.escolha.q,30)

    def test_q_valido_preservado_ev02(self):
        e = EstadoIndividual(); selecionar_otimo(e)
        evento(e,"cf",1600)
        self.assertEqual(e.escolha.q,80/3)
        evento(e,"c",40)
        self.assertEqual(e.escolha.q,80/3)

    def test_trocas_preservam_escolha_ev03(self):
        e = EstadoIndividual(); selecionar_otimo(e)
        original = e.escolha
        for vista in ("Análise Marginal","Resultados Totais"):
            for foco in ("Geral","Receita total","Custo total","Lucro"):
                selecionar_vista(e,vista,foco)
                e.mostrar_otimos = not e.mostrar_otimos
                self.assertEqual(e.escolha,original)

    def test_sequencia_ignora_repetidos_e_atrasados(self):
        e = EstadoIndividual(); evento(e,"q",30)
        self.assertFalse(aplicar_evento(e,"q",{"seq":1,"fase":"fim","valor":60}))
        self.assertFalse(aplicar_evento(e,"q",{"seq":True,"fase":"fim","valor":60}))
        self.assertEqual(e.escolha.q,30)

    def test_sessoes_independentes(self):
        e = EstadoIndividual(); evento(e,"q",75)
        outro = EstadoIndividual()
        self.assertEqual(outro.escolha.q,25)
        self.assertIsNot(e.erros,outro.erros)

    def test_hot_reload_reconstroi_contratos_sem_perder_precisao(self):
        e = EstadoIndividual(); selecionar_otimo(e)
        e.escolha = SimpleNamespace(q=80/3,parametros=SimpleNamespace(a=100,b=1,c=20,s=1,cf=0))
        novo = revalidar_sessao(e)
        self.assertIsInstance(novo.escolha.parametros,ParametrosFirma)
        self.assertEqual(novo.escolha.q,80/3)
        self.assertEqual(novo.confirmado.q,80/3)
        self.assertIsNot(novo.sequencias,e.sequencias)

    def test_rerun_com_classes_vigentes_preserva_objeto_canonico(self):
        e = EstadoIndividual()
        self.assertIs(revalidar_sessao(e),e)

    def test_eventos_incorretos_nao_criam_estado(self):
        e = EstadoIndividual()
        for campo, payload in (("x",{}),("q",None),("q",{"seq":2,"fase":"inesperada"})):
            self.assertFalse(aplicar_evento(e,campo,payload))
        self.assertEqual(e.escolha,Escolha())


class Mensagens(unittest.TestCase):
    def test_classes_da_quantidade(self):
        for q, trecho in ((0,"abaixo"),(25,"abaixo"),(26.67,"muito próxima"),(80/3,"maximiza"),(75,"acima")):
            self.assertIn(trecho,mensagem_quantidade(Escolha(q=q)))

    def test_cf_exclusivo_e_base_da_ultima_mudanca(self):
        e = EstadoIndividual(); evento(e,"cf",400)
        self.assertIn("custo fixo aumentou e reduziu",sintese(e))
        evento(e,"q",30)
        self.assertNotIn("custo fixo aumentou",sintese(e))
        evento(e,"cf",100)
        self.assertIn("custo fixo diminuiu e elevou",sintese(e))

    def test_alteracoes_conjuntas_sem_causalidade_exclusiva(self):
        e = EstadoIndividual()
        atualizar_parametros(e,ParametrosFirma(a=120,c=40,cf=100)); confirmar(e)
        self.assertIn("alterações simultâneas",sintese(e))
        self.assertNotIn("custo fixo aumentou",sintese(e))

    def test_fronteiras_sem_otimo_interior(self):
        for c, trecho in ((100,"igualdade na fronteira"),(120,"RMg(0)<CMg(0)")):
            escolha = Escolha(ParametrosFirma(c=c),0)
            self.assertIn("não produzir",mensagem_quantidade(escolha))
            self.assertIn(trecho,mensagem_marginal(escolha))
            self.assertIn("hipotética"," ".join(condicoes_excepcionais(replace(escolha,q=10))))

    def test_marginais_nao_usam_proximidade_como_igualdade(self):
        self.assertIn("reduzir",mensagem_marginal(Escolha(q=26.67)))
        self.assertNotIn("se igualam",mensagem_marginal(Escolha(q=26.67)))
        self.assertIn("elevar",mensagem_marginal(Escolha(q=25)))
        self.assertIn("resíduo",mensagem_marginal(Escolha(q=80/3)))

    def test_limite_superior_nao_recomenda_expansao(self):
        texto = mensagem_marginal(Escolha(q=100))
        self.assertIn("não é admissível",texto)
        self.assertNotIn("tende a elevar",texto)

    def test_preco_em_zero_e_lucro_negativo(self):
        avisos = " ".join(condicoes_excepcionais(Escolha(ParametrosFirma(cf=1600),0)))
        self.assertIn("não existe preço efetivamente transacionado",avisos)
        self.assertIn("não decide o fechamento",avisos)

    def test_otimo_minusculo_nao_rotula_zero_otimo(self):
        p = ParametrosFirma(c=math.nextafter(100,0))
        self.assertIn("abaixo",mensagem_quantidade(Escolha(p,0)))

    def test_formatacao_ptbr_sem_alterar_entrada_ou_falso_zero(self):
        self.assertEqual(numero(1875),"1.875,00")
        self.assertEqual(numero(-50),"-50,00")
        self.assertNotEqual(numero(-1e-14),"-0,00")
        self.assertEqual(ler_numero("26,666666666666668"),80/3)

    def test_niveis_opcionais(self):
        for nivel in ("Essencial","Econômica","Matemática"):
            self.assertTrue(explicacao(Escolha(),nivel))
        self.assertIn("não previsões",explicacao(Escolha(),"Econômica"))
        self.assertIn("não é necessariamente",explicacao(Escolha(),"Econômica"))


class Graficos(unittest.TestCase):
    def test_inicial_sem_otimos(self):
        fig = grafico_individual(EstadoIndividual())
        self.assertEqual([t.name for t in fig.data if t.mode == "lines"], ["Receita total","Custo total","Lucro"])
        self.assertFalse(any(t.meta and t.meta.get("papel")=="otimo" for t in fig.data))

    def test_marginal_negativa_at03(self):
        e = EstadoIndividual(escolha=Escolha(q=75),perspectiva="Análise Marginal")
        fig = grafico_individual(e)
        pontos = [t for t in fig.data if t.meta and t.meta.get("papel")=="escolha"]
        self.assertEqual([list(t.y) for t in pontos],[[-50],[95]])
        self.assertLessEqual(fig.layout.yaxis.range[0],-100)
        self.assertTrue(any(s.y0==0 and s.y1==0 for s in fig.layout.shapes))

    def test_focos_preservam_dados_e_unidades(self):
        e = EstadoIndividual(escolha=Escolha(ParametrosFirma(cf=1600),80/3))
        for foco, esperado in (("Receita total",17600/9),("Custo total",22400/9),("Lucro",-1600/3)):
            e.foco = foco
            fig = grafico_individual(e)
            pontos = [t for t in fig.data if t.meta and t.meta.get("papel")=="escolha"]
            self.assertAlmostEqual(pontos[0].y[0],esperado)
            self.assertEqual(fig.layout.yaxis.title.text,"u.m.")
            self.assertEqual(e.escolha.q,80/3)

    def test_otimos_pertinentes_e_guias_rotuladas(self):
        e = EstadoIndividual(mostrar_otimos=True)
        for foco, quantidade_otimos in (("Geral",2),("Receita total",1),("Custo total",0),("Lucro",1)):
            e.foco = foco; fig = grafico_individual(e)
            otimos = [t for t in fig.data if t.meta and t.meta.get("papel")=="otimo"]
            self.assertEqual(len(otimos),quantidade_otimos)
            for t in otimos:
                self.assertIn(t.meta["funcao"], ("receita_total","lucro"))
                if t.meta["funcao"]=="receita_total":
                    self.assertEqual(t.y[0],2500)
                else:
                    self.assertAlmostEqual(t.y[0],3200/3)
            if foco == "Custo total":
                self.assertEqual(len(fig.layout.annotations),2)
                self.assertTrue(all("referência" in a.text for a in fig.layout.annotations))

    def test_fronteira_sem_cruzamento_nao_cria_marcador(self):
        e = EstadoIndividual(escolha=Escolha(ParametrosFirma(c=120),0),mostrar_otimos=True,perspectiva="Análise Marginal")
        fig = grafico_individual(e)
        self.assertFalse(any(t.meta and t.meta.get("papel")=="otimo" for t in fig.data))
        self.assertTrue(any("fronteira" in a.text for a in fig.layout.annotations))

    def test_dominio_entre_ticks_e_sem_arredondar(self):
        e = EstadoIndividual(escolha=Escolha(ParametrosFirma(b=1.1537),25.123456789))
        fig = grafico_individual(e)
        for t in fig.data:
            self.assertGreaterEqual(min(t.x),0)
            self.assertLessEqual(max(t.x),100/1.1537)
        self.assertEqual(fig.data[1].x[0],25.123456789)
        self.assertEqual(fig.layout.transition.duration,0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
