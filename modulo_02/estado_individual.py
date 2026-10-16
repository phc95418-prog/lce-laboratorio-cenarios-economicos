"""Estado e eventos de A individual; nenhum resultado econômico em cache."""

from dataclasses import dataclass, field, replace
from collections.abc import MutableMapping
import re

from .modelo_firma import calcular_otimos
from .validacao import ParametrosFirma, limitar_quantidade, numero_finito, validar_quantidade

LIMITES = {"a": (60, 140, 5), "b": (0.5, 2, 0.1), "c": (0, 160, 5),
           "s": (0.25, 3, 0.25), "cf": (0, 1600, 100)}
PERSPECTIVAS = ("Resultados Totais", "Análise Marginal")
FOCOS = ("Geral", "Receita total", "Custo total", "Lucro")


@dataclass(frozen=True)
class Escolha:
    parametros: ParametrosFirma = field(default_factory=ParametrosFirma)
    q: float = 25.0


@dataclass
class EstadoIndividual:
    escolha: Escolha = field(default_factory=Escolha)
    confirmado: Escolha = field(default_factory=Escolha)
    anterior: Escolha = field(default_factory=Escolha)
    perspectiva: str = PERSPECTIVAS[0]
    foco: str = FOCOS[0]
    mostrar_otimos: bool = False
    interagiu: bool = False
    em_interacao: bool = False
    sequencias: dict = field(default_factory=dict)
    erros: dict = field(default_factory=dict)
    aviso_dominio: str = ""
    zoom: dict[str, int] = field(default_factory=dict)


def revalidar_sessao(estado: EstadoIndividual) -> EstadoIndividual:
    """Reconstitui contratos após hot reload, preservando escolhas da sessão.

    Streamlit pode recarregar classes Python enquanto session_state retém
    instâncias das classes antigas. Dados válidos sobrevivem sem relaxar os
    testes de tipo do motor e sem persistência externa ao navegador.
    """
    if type(estado) is EstadoIndividual and all(
        type(getattr(estado,nome)) is Escolha and
        type(getattr(estado,nome).parametros) is ParametrosFirma
        for nome in ("escolha", "confirmado", "anterior")
    ):
        return estado
    escolhas = {}
    for nome in ("escolha", "confirmado", "anterior"):
        origem = getattr(estado, nome)
        p = ParametrosFirma(**{campo:getattr(origem.parametros,campo) for campo in LIMITES})
        escolhas[nome] = Escolha(p, validar_quantidade(origem.q,p))
    return EstadoIndividual(
        **escolhas, perspectiva=estado.perspectiva, foco=estado.foco,
        mostrar_otimos=estado.mostrar_otimos, interagiu=estado.interagiu,
        em_interacao=estado.em_interacao, sequencias=dict(estado.sequencias),
        erros=dict(estado.erros), aviso_dominio=estado.aviso_dominio,
        zoom=dict(getattr(estado, "zoom", {})),
    )


def ler_numero(texto: str) -> float:
    if not isinstance(texto, str) or not re.fullmatch(
        r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:[eE][+-]?\d+)?", texto.strip()
    ):
        raise ValueError("Confirme um número completo e válido.")
    return numero_finito(float(texto.strip().replace(",", ".")), "Valor")


def confirmar(estado: EstadoIndividual) -> None:
    estado.anterior = estado.confirmado
    estado.confirmado = estado.escolha
    estado.em_interacao = False
    estado.interagiu = True


def atualizar_parametros(estado: EstadoIndividual, parametros: ParametrosFirma) -> None:
    """Mudanças conjuntas são suportadas sem implementar comparação de cenários."""
    if not isinstance(parametros, ParametrosFirma):
        raise TypeError("Use ParametrosFirma.")
    q = limitar_quantidade(estado.escolha.q, parametros)
    if q != estado.escolha.q:
        estado.aviso_dominio = (
            "Q ajustada ao máximo permitido pelo novo domínio."
        )
    estado.escolha = Escolha(parametros, q)


def aplicar_evento(estado: EstadoIndividual, campo: str, evento: dict) -> bool:
    """Revalida eventos do componente. Live calcula; fim/Enter/blur consolidam."""
    if campo not in (*LIMITES, "q") or not isinstance(evento, dict):
        return False
    seq = evento.get("seq")
    if type(seq) is not int or seq <= estado.sequencias.get(campo, 0):
        return False
    fase = evento.get("fase")
    if fase not in ("live", "fim", "campo", "invalido"):
        return False
    estado.sequencias[campo] = seq
    try:
        valor = ler_numero(evento.get("texto")) if fase in ("campo", "invalido") else numero_finito(evento.get("valor"), campo)
        if campo == "q":
            q = validar_quantidade(valor, estado.escolha.parametros)
            estado.escolha = Escolha(estado.escolha.parametros, q)
            estado.aviso_dominio = ""
        else:
            parametros = replace(estado.escolha.parametros, **{campo: valor})
            atualizar_parametros(estado, parametros)
        estado.erros.pop(campo, None)
        if fase == "live":
            estado.em_interacao = True
        else:
            confirmar(estado)
    except (ValueError, TypeError, OverflowError) as erro:
        estado.erros[campo] = str(erro)
    return True


def selecionar_otimo(estado: EstadoIndividual) -> None:
    p = estado.escolha.parametros
    estado.escolha = Escolha(p, calcular_otimos(p).q_lucro)
    estado.erros.pop("q", None)
    estado.aviso_dominio = ""
    confirmar(estado)


def selecionar_vista(estado: EstadoIndividual, perspectiva: str, foco: str | None = None) -> None:
    if perspectiva not in PERSPECTIVAS or (foco is not None and foco not in FOCOS):
        raise ValueError("Perspectiva ou foco inválido.")
    estado.perspectiva = perspectiva
    if foco is not None:
        estado.foco = foco


def chave_visualizacao(estado: EstadoIndividual) -> str:
    return "marginal" if estado.perspectiva == "Análise Marginal" else f"totais:{estado.foco}"


def alterar_zoom(estado: EstadoIndividual, acao: str) -> None:
    """Zoom de apresentação por vista, sem alterar a escolha econômica."""
    chave = chave_visualizacao(estado)
    nivel = estado.zoom.get(chave, 0)
    if acao == "ampliar":
        nivel = min(4, nivel + 1)
    elif acao == "reduzir":
        nivel = max(0, nivel - 1)
    elif acao == "restaurar":
        nivel = 0
    else:
        raise ValueError("Ação de zoom inválida.")
    estado.zoom[chave] = nivel


def restaurar_experimento(sessao: MutableMapping) -> None:
    """Reinicia apenas A individual, inclusive widgets e rascunhos pendentes.

    Uma geração nova remonta os controles no navegador. Eventos tardios da
    geração descartada não podem reintroduzir valores ou mensagens antigas.
    """
    geracao = sessao.get("m02_a_geracao", 0) + 1
    for chave in list(sessao):
        if chave.startswith("m02_a_"):
            del sessao[chave]
    sessao["m02_a_geracao"] = geracao
    sessao["m02_a_individual"] = EstadoIndividual()


def aplicar_evento_sessao(sessao: MutableMapping, geracao: int, campo: str, evento: dict) -> bool:
    if geracao != sessao.get("m02_a_geracao", 0):
        return False
    estado = revalidar_sessao(sessao["m02_a_individual"])
    aplicado = aplicar_evento(estado, campo, evento)
    sessao["m02_a_individual"] = estado
    return aplicado
