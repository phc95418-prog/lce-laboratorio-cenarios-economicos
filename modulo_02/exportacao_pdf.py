"""SVG capturado pelo Plotly → PDF vetorial por Chromium local, sem instalar bibliotecas."""
from base64 import b64encode
from functools import lru_cache
from pathlib import Path
import math
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


@lru_cache(maxsize=1)
def navegador_pdf():
    candidatos=[shutil.which(n) for n in ("google-chrome","chromium","chromium-browser","msedge")]
    if os.name=="nt":
        candidatos += [str(Path(os.environ.get(base,"C:/Program Files"))/p) for base,p in (
            ("PROGRAMFILES","Google/Chrome/Application/chrome.exe"),
            ("PROGRAMFILES(X86)","Microsoft/Edge/Application/msedge.exe"))]
    return next((p for p in candidatos if p and Path(p).is_file()),None)


def validar_svg(svg):
    if not isinstance(svg,str) or len(svg.encode("utf-8"))>4_000_000:
        raise ValueError("SVG ausente ou excessivamente grande.")
    if re.search(r"<!DOCTYPE|<!ENTITY",svg,re.I): raise ValueError("SVG com declaração não permitida.")
    try: raiz=ET.fromstring(svg)
    except ET.ParseError as erro: raise ValueError("SVG inválido.") from erro
    if raiz.tag.split("}")[-1]!="svg": raise ValueError("O arquivo não é SVG.")
    for el in raiz.iter():
        if el.tag.split("}")[-1] in ("script","foreignObject"):
            raise ValueError("SVG contém elemento não permitido.")
        for nome,valor in el.attrib.items():
            local=nome.split("}")[-1].lower()
            if local.startswith("on") or (local=="href" and not valor.startswith(("#","data:image/"))):
                raise ValueError("SVG contém referência externa ou evento.")
            if re.search(r"url\(\s*['\"]?(?!#)[a-zA-Z]",valor,re.I):
                raise ValueError("SVG contém recurso externo.")
    try:
        w,h=(float(raiz.attrib[n].removesuffix("px")) for n in ("width","height"))
    except (KeyError,ValueError) as erro: raise ValueError("SVG sem dimensões válidas.") from erro
    if not all(math.isfinite(v) and 4<=v<=16000 for v in (w,h)):
        raise ValueError("Dimensões do SVG fora do limite.")
    return w,h


def gerar_pdf(svg):
    w,h=validar_svg(svg)
    navegador=navegador_pdf()
    if not navegador: raise RuntimeError("PDF indisponível: não há Chrome/Chromium compatível neste ambiente.")
    imagem=b64encode(svg.encode("utf-8")).decode("ascii")
    html=(f'<!doctype html><html><head><meta charset="utf-8"><style>@page{{size:{w}px {h}px;margin:0}}'
          f'html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden;print-color-adjust:exact;-webkit-print-color-adjust:exact}}'
          'img{display:block;width:100%;height:100%}</style></head><body>'
          f'<img alt="Gráfico do LCE" src="data:image/svg+xml;base64,{imagem}"></body></html>')
    # Diretório recém-criado sob o temporário do sistema; nunca recebe caminho do cliente.
    with tempfile.TemporaryDirectory(prefix="lce-pdf-",ignore_cleanup_errors=True) as pasta:
        raiz=Path(pasta).resolve()
        if raiz.parent!=Path(tempfile.gettempdir()).resolve(): raise RuntimeError("Diretório temporário inesperado.")
        entrada=raiz/"grafico.html";saida=raiz/"grafico.pdf"
        entrada.write_text(html,encoding="utf-8")
        comando=[navegador,"--headless=new","--no-first-run","--no-default-browser-check",
            f"--user-data-dir={raiz/'perfil'}",f"--print-to-pdf={saida}","--no-pdf-header-footer",entrada.as_uri()]
        try:
            resultado=subprocess.run(comando,capture_output=True,timeout=25,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except (OSError,subprocess.TimeoutExpired) as erro:
            raise RuntimeError("Não foi possível concluir a geração do PDF neste ambiente.") from erro
        if resultado.returncode or not saida.is_file(): raise RuntimeError("O navegador não gerou um PDF.")
        pdf=saida.read_bytes()
    if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:]:
        raise RuntimeError("PDF gerado sem estrutura válida.")
    return pdf
