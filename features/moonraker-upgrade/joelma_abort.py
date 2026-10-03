# joelma_abort.py - expoe o endpoint Klipper force_stop_homing (feature
# abort_homing) via REST, pra a Central disparar o "Parar Homing". Usa o MESMO
# caminho interno do emergency_stop do Moonraker (_send_klippy_request). Faz
# parte do fork k2-improvements-joelma.
#
# Endpoint:
#   POST /server/joelma/abort_homing  -> chama force_stop_homing no Klipper
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest


class JoelmaAbort:
    def __init__(self, config: "ConfigHelper") -> None:
        self.server = config.get_server()
        self.server.register_endpoint(
            "/server/joelma/abort_homing",
            RequestType.POST,
            self._handle,
        )

    async def _handle(self, web_request: "WebRequest") -> Dict[str, Any]:
        kapis = self.server.lookup_component("klippy_apis")
        try:
            # mesmo caminho que o emergency_stop do Moonraker usa internamente
            await kapis._send_klippy_request("force_stop_homing", {})
        except Exception as e:
            raise self.server.error("force_stop_homing falhou: %s" % e, 500)
        return {"ok": True}


def load_component(config: "ConfigHelper") -> JoelmaAbort:
    return JoelmaAbort(config)
