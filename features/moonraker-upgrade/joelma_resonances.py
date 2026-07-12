# joelma_resonances.py - componente Moonraker que expoe os CSVs de ressonancia
# que o Klipper grava em /tmp (TEST_RESONANCES e SHAPER_CALIBRATE) para a
# Central de Calibracao desenhar os graficos direto no navegador, via REST.
#
# Endpoints:
#   GET /server/joelma/resonances            -> {"arquivos":[{nome,bytes,mtime}]}
#   GET /server/joelma/resonances/csv?nome=X -> {"nome","colunas":[...],"dados":[[...]]}
#
# Seguranca: le SOMENTE /tmp e SOMENTE nomes no padrao do Klipper
# (resonances_*.csv / calibration_data_*.csv) — sem path traversal.
#
# Faz parte do fork k2-improvements-joelma.
from __future__ import annotations
import os
import re
from typing import TYPE_CHECKING, Any, Dict, List

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest

DIRETORIO = "/tmp"
PADRAO = re.compile(r"^(resonances|calibration_data)_[a-z]+_[A-Za-z0-9_.-]+\.csv$")
MAX_LINHAS = 4000  # PSD tem ~200 linhas; limite protege contra arquivo anomalo


class JoelmaResonances:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.server.register_endpoint(
            "/server/joelma/resonances", RequestType.GET, self._lista,
        )
        self.server.register_endpoint(
            "/server/joelma/resonances/csv", RequestType.GET, self._csv,
        )

    async def _lista(self, web_request: WebRequest) -> Dict[str, Any]:
        arqs: List[Dict[str, Any]] = []
        try:
            for nome in os.listdir(DIRETORIO):
                if not PADRAO.match(nome):
                    continue
                st = os.stat(os.path.join(DIRETORIO, nome))
                arqs.append(
                    {"nome": nome, "bytes": st.st_size, "mtime": int(st.st_mtime)}
                )
        except OSError:
            pass
        arqs.sort(key=lambda a: a["mtime"], reverse=True)
        return {"arquivos": arqs}

    async def _csv(self, web_request: WebRequest) -> Dict[str, Any]:
        nome = web_request.get_str("nome")
        if not PADRAO.match(nome):
            raise self.server.error("nome de arquivo invalido", 400)
        caminho = os.path.join(DIRETORIO, nome)
        if not os.path.isfile(caminho):
            raise self.server.error("arquivo nao encontrado", 404)
        colunas: List[str] = []
        dados: List[List[float]] = []
        with open(caminho, "r", errors="replace") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                # 1a linha com letras = cabecalho ("freq,psd_x,..." ou "#...")
                if not colunas and re.search(r"[A-Za-z]", linha):
                    colunas = linha.lstrip("#").split(",")
                    continue
                try:
                    dados.append([float(x) for x in linha.split(",")])
                except ValueError:
                    continue
                if len(dados) >= MAX_LINHAS:
                    break
        if not colunas and dados:
            colunas = ["c%d" % i for i in range(len(dados[0]))]
        return {"nome": nome, "colunas": colunas, "dados": dados}


def load_component(config: ConfigHelper) -> JoelmaResonances:
    return JoelmaResonances(config)
