"""Transições de comparação de A (EV-04–11), sem fórmulas econômicas novas."""

from dataclasses import dataclass, field, replace

from .estado_individual import LIMITES, confirmar, atualizar_parametros, ler_numero
from .modelo_firma import avaliar_firma, calcular_otimos
from .validacao import ParametrosFirma, numero_finito

PERSPECTIVAS = ("Quantidade fixa", "Decisões ótimas")


@dataclass
class EstadoComparacao:
    referencia: ParametrosFirma
    q_fixa: float
    q_confirmada: float
    perspectiva: str = PERSPECTIVAS[0]
    foco: str = "Geral"
    sequencia: int = 0
    erro: str = ""
    aviso: str = ""
    substituindo: bool = False
    revisao: int = 0


def revalidar_comparacao(c):
    if type(c) is EstadoComparacao and type(c.referencia) is ParametrosFirma:
        return c
    return EstadoComparacao(**{
        **vars(c), "referencia": ParametrosFirma(**{k:getattr(c.referencia,k) for k in LIMITES})
    })


def dominio_comum(estado):
    return min(estado.escolha.parametros.q_max, estado.comparacao.referencia.q_max)


def revalidar_dominios(estado):
    c = estado.comparacao
    limite = dominio_comum(estado)
    c.q_confirmada = min(c.q_confirmada, limite)
    if c.q_fixa > limite:
        antes = c.q_fixa
        c.q_fixa = limite
        c.erro = ""
        origem, destino = (f"{v:g}".replace(".",",") for v in (antes,limite))
        c.aviso = f"Q da comparação foi limitada de {origem} para {destino} pelo domínio comum."


def fixar_referencia(estado):
    if estado.comparacao is not None:
        raise ValueError("Use a substituição confirmada para uma comparação ativa.")
    estado.ciclo_comparacao += 1
    p = replace(estado.escolha.parametros)
    q = min(estado.escolha.q, p.q_max)
    estado.comparacao = EstadoComparacao(p, q, q)
    if q < estado.escolha.q:
        estado.comparacao.aviso = "Q da comparação foi limitada pelo domínio comum."


def substituir_referencia(estado, confirmar_substituicao):
    c = estado.comparacao
    if confirmar_substituicao:
        c.referencia = replace(estado.escolha.parametros)
        revalidar_dominios(estado)
    c.substituindo = False


def restaurar_parametros(estado):
    atualizar_parametros(estado, ParametrosFirma())
    for campo in LIMITES:
        estado.erros.pop(campo,None)
    revalidar_dominios(estado)
    confirmar(estado)


def encerrar_comparacao(estado):
    estado.comparacao = None


def aplicar_quantidade(estado, evento):
    c = estado.comparacao
    if c is None or c.perspectiva != PERSPECTIVAS[0]:
        return False
    if not isinstance(evento, dict) or type(evento.get("seq")) is not int or evento["seq"] <= c.sequencia:
        return False
    fase = evento.get("fase")
    if fase not in ("live", "fim", "campo", "invalido"):
        return False
    c.sequencia = evento["seq"]
    try:
        q = ler_numero(evento.get("texto")) if fase in ("campo", "invalido") else numero_finito(evento.get("valor"), "Q")
        if not 0 <= q <= dominio_comum(estado):
            raise ValueError("Q deve pertencer ao domínio comum dos dois cenários.")
        c.q_fixa = q
        c.erro = ""
        if fase != "live":
            c.q_confirmada = q
        return True
    except (ValueError, TypeError, OverflowError) as erro:
        c.erro = str(erro)
        return False


def resultados_comparacao(estado, consolidada=False):
    c = estado.comparacao
    atual = estado.confirmado.parametros if consolidada else estado.escolha.parametros
    qr = qa = c.q_confirmada if consolidada else c.q_fixa
    if c.perspectiva == PERSPECTIVAS[1]:
        qr = calcular_otimos(c.referencia).q_lucro
        qa = calcular_otimos(atual).q_lucro
    # Um domínio que encolheu vale imediatamente, inclusive para a síntese.
    qr, qa = min(qr,c.referencia.q_max), min(qa,atual.q_max)
    r, a = avaliar_firma(qr,c.referencia), avaliar_firma(qa,atual)
    diferencas = {"Quantidade":qa-qr, "Receita total":a.curvas.receita_total-r.curvas.receita_total,
                  "Custo total":a.custo_total-r.custo_total, "Lucro":a.lucro-r.lucro}
    return r, a, diferencas
