"""Transições de B: parâmetros próprios, importação pontual e áreas exclusivas."""
from dataclasses import dataclass, field, replace
from .validacao import ParametrosMercado, numero_finito
from .estado_individual import ler_numero

MODOS = ("Comparar resultados", "Entender o mecanismo", "Investigar o bem-estar")
REGIOES = ("EC", "EP", "DWL")
REGIMES = ("Concorrência", "Monopólio")
PARCELAS = ("DWL", "T", "L_C", "L_P")
CAMPOS = ("a", "b", "c", "s")


@dataclass
class EstadoB:
    parametros: ParametrosMercado = field(default_factory=ParametrosMercado)
    confirmado: ParametrosMercado = field(default_factory=ParametrosMercado)
    anterior: ParametrosMercado = field(default_factory=ParametrosMercado)
    modo: str = MODOS[0]
    regiao: str = "EC"
    regime: str = REGIMES[0]
    decomposicao: bool = False
    selecao_guardada: tuple | None = None
    parcela: str = "DWL"
    sequencias: dict = field(default_factory=dict)
    erros: dict = field(default_factory=dict)
    em_interacao: bool = False
    aviso: str = ""
    zoom: dict = field(default_factory=dict)
    roda: bool = False


def revalidar_b(e):
    if type(e) is EstadoB and all(type(getattr(e,k)) is ParametrosMercado for k in ("parametros","confirmado","anterior")):
        return e
    dados=dict(vars(e))
    for k in ("parametros","confirmado","anterior"):
        dados[k]=ParametrosMercado(**{c:getattr(dados[k],c) for c in CAMPOS})
    return EstadoB(**dados)


def confirmar_b(e):
    e.anterior=e.confirmado
    e.confirmado=e.parametros
    e.em_interacao=False


def aplicar_evento_b(e,campo,evento):
    if campo not in CAMPOS or not isinstance(evento,dict): return False
    seq,fase=evento.get("seq"),evento.get("fase")
    if type(seq) is not int or seq<=e.sequencias.get(campo,0) or fase not in ("live","fim","campo","invalido"):
        return False
    e.sequencias[campo]=seq
    try:
        v=ler_numero(evento.get("texto")) if fase in ("campo","invalido") else numero_finito(evento.get("valor"),campo)
        e.parametros=replace(e.parametros,**{campo:v})
        e.erros.pop(campo,None)
        if fase=="live": e.em_interacao=True
        else: confirmar_b(e)
    except (ValueError,TypeError,OverflowError) as erro:
        e.erros[campo]=str(erro)
    return True


def importar_de_a(e,origem):
    if origem is None:
        e.aviso="Parâmetros do Experimento A indisponíveis nesta sessão. Nenhum valor foi importado."
        return False
    p=origem.escolha.parametros
    e.parametros=ParametrosMercado(**{k:getattr(p,k) for k in CAMPOS})
    confirmar_b(e)
    e.erros.clear()
    e.aviso="Parâmetros a, b, c e s copiados do Atual de A, sem CF. Não há sincronização posterior."
    return True


def abrir_decomposicao(e):
    if not e.decomposicao:
        e.selecao_guardada=(e.regiao,e.regime)
        e.decomposicao=True
        e.parcela="DWL"


def fechar_decomposicao(e):
    if e.decomposicao:
        e.regiao,e.regime=e.selecao_guardada
        e.decomposicao=False
        e.selecao_guardada=None


def regiao_ativa(e):
    return e.parcela if e.decomposicao else e.regiao


def reiniciar_controles(sessao):
    """Remonta buffers após ação programática, sem apagar as seleções de B."""
    sessao["m02_b_geracao"]=sessao.get("m02_b_geracao",0)+1


def restaurar_parametros_b(e):
    e.parametros=ParametrosMercado()
    confirmar_b(e)
    e.erros.clear()
    e.aviso="Parâmetros padrão do B restaurados; modos e seleções preservados."
