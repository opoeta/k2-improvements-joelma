# joelma_info.py - componente Moonraker que expoe a versao do firmware da
# impressora (o OTA da Creality), que nem o Klipper nem o Moonraker reportam.
#
# A Creality guarda a versao numa variavel do U-Boot, nao em arquivo:
#   /etc/ota_bin/get_ota_current_version.sh  ->  fw_printenv version
# (ler /etc/os-release daria a versao do OpenWrt, que NAO e o firmware.)
#
# Endpoint:
#   GET /server/joelma/info -> {firmware, board, modelo, modelo_cod}
#
# Faz parte do fork k2-improvements-joelma.
from __future__ import annotations
import asyncio
import logging
import re
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest

# codigos de modelo da Creality -> nome legivel
MODELOS = {"F008": "K2 Plus", "F012": "K2 Pro", "F021": "K2",
           "F022": "SPARKX i7", "F018": "Hi"}


class JoelmaInfo:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.cache: Optional[Dict[str, Any]] = None
        self.server.register_endpoint(
            "/server/joelma/info",
            RequestType.GET,
            self._handle_info,
        )
        logging.info("joelma_info: endpoint registrado")

    async def _uboot(self, chave: str) -> Optional[str]:
        # fw_printenv <chave> -> "chave=valor"
        try:
            proc = await asyncio.create_subprocess_exec(
                "fw_printenv", chave,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        except Exception:
            return None
        txt = out.decode("utf-8", "replace").strip()
        if "=" not in txt:
            return None
        valor = txt.split("=", 1)[1].strip()
        return valor or None

    async def _modelo(self) -> Dict[str, Optional[str]]:
        # a API stock da Creality (porta 80) responde /info com o codigo do modelo
        try:
            fut = asyncio.open_connection("127.0.0.1", 80)
            reader, writer = await asyncio.wait_for(fut, timeout=2)
            writer.write(b"GET /info HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                         b"Connection: close\r\n\r\n")
            await writer.drain()
            data = await asyncio.wait_for(reader.read(1024), timeout=2)
            writer.close()
        except Exception:
            return {"modelo": None, "modelo_cod": None}
        corpo = data.decode("utf-8", "replace").split("\r\n\r\n", 1)[-1]
        m = re.search(r'"model"\s*:\s*"([^"]+)"', corpo)
        if not m:
            return {"modelo": None, "modelo_cod": None}
        cod = m.group(1)
        return {"modelo": MODELOS.get(cod, cod), "modelo_cod": cod}

    async def _handle_info(self, web_request: WebRequest) -> Dict[str, Any]:
        if self.cache is not None:
            return self.cache
        d: Dict[str, Any] = {
            "firmware": await self._uboot("version"),
            "board": await self._uboot("board"),
        }
        d.update(await self._modelo())
        self.cache = d
        return d


def load_component(config: ConfigHelper) -> JoelmaInfo:
    return JoelmaInfo(config)
