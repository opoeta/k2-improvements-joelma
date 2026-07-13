# joelma_cfs_edit.py - componente Moonraker que edita material/cor de um slot
# do CFS GRAVANDO NO FIRMWARE, nos mesmos arquivos que a tela da impressora usa
# (descobertos empiricamente em jul/2026 editando um slot na tela e vendo o que
# mudou no disco):
#
#   /mnt/UDISK/creality/userdata/box/material_modify_info.json  (overlay de edicoes)
#   /mnt/UDISK/creality/userdata/box/material_box_info.json     (estado corrente)
#
# Com a edicao gravada ai, tela, Creality Print e OrcaSlicer (porta 9999,
# boxsInfo) passam a ver o mesmo material/cor — e o que o rotulo em
# localStorage da Central nunca conseguiu fazer.
#
# Endpoints:
#   GET  /server/joelma/cfs/edit -> conteudo dos dois JSONs
#   POST /server/joelma/cfs/edit -> edita um slot
#        body: {"tnn":"T1D","materialType":"PLA","color":"#RRGGBB",
#               "name":"apelido","brand":"Generic",
#               "minTemp":190,"maxTemp":240,"pressure":"0.04"}   (3 ultimos opcionais)
#
# Escrita atomica (tmp + replace). So slots T1A..T4D.
#
# Faz parte do fork k2-improvements-joelma.
from __future__ import annotations
import json
import os
import re
from typing import TYPE_CHECKING, Any, Dict

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest

DIR_BOX = "/mnt/UDISK/creality/userdata/box"
ARQ_MODIFY = os.path.join(DIR_BOX, "material_modify_info.json")
ARQ_BOX = os.path.join(DIR_BOX, "material_box_info.json")

# codigo Creality por material (mesma tabela da Central)
FILAMENT_ID = {
    "PLA": "000001", "PETG": "002001", "ABS": "003001", "TPU": "004001",
    "ASA": "005001", "PA": "006001", "PC": "007001",
}
# faixas de temperatura padrao por material (min, max)
TEMPS = {
    "PLA": (190, 240), "PETG": (220, 270), "ABS": (240, 280), "ASA": (240, 280),
    "TPU": (200, 240), "PA": (260, 300), "PC": (260, 300),
}


def _le(caminho: str) -> Dict[str, Any]:
    with open(caminho, "r") as f:
        return json.load(f)


def _grava(caminho: str, dados: Dict[str, Any]) -> None:
    tmp = caminho + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    os.replace(tmp, caminho)


class JoelmaCfsEdit:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.server.register_endpoint(
            "/server/joelma/cfs/edit",
            RequestType.GET | RequestType.POST,
            self._handle,
        )

    async def _handle(self, web_request: WebRequest) -> Dict[str, Any]:
        if web_request.get_request_type() == RequestType.POST:
            return self._edita(web_request)
        saida: Dict[str, Any] = {}
        for rotulo, caminho in (("modify", ARQ_MODIFY), ("box", ARQ_BOX)):
            try:
                saida[rotulo] = _le(caminho)
            except OSError:
                saida[rotulo] = None
        return saida

    def _edita(self, web_request: WebRequest) -> Dict[str, Any]:
        tnn = web_request.get_str("tnn").upper().strip()
        if not re.match(r"^T[1-4][A-D]$", tnn):
            raise self.server.error("tnn invalido (esperado T1A..T4D)", 400)
        mat = web_request.get_str("materialType").upper().strip()
        cor = web_request.get_str("color").strip()
        if not re.match(r"^#[0-9a-fA-F]{6}$", cor):
            raise self.server.error("color invalida (esperado #RRGGBB)", 400)
        nome = web_request.get_str("name", "").strip() or mat
        marca = web_request.get_str("brand", "Generic").strip() or "Generic"
        base = mat.split("-")[0]  # PLA-CF usa a base PLA p/ codigo e temps
        tmin_def, tmax_def = TEMPS.get(base, (190, 260))
        tmin = int(web_request.get_int("minTemp", tmin_def))
        tmax = int(web_request.get_int("maxTemp", tmax_def))
        pressao = str(web_request.get_str("pressure", "")).strip()

        box_i = int(tnn[1]) - 1          # T1->0
        slot_i = ord(tnn[2]) - ord("A")  # A->0
        cor_fw = "#0" + cor[1:].lower()  # formato Creality "#0RRGGBB"
        fil_id = FILAMENT_ID.get(base, "000001")

        if not (os.path.isfile(ARQ_MODIFY) and os.path.isfile(ARQ_BOX)):
            raise self.server.error(
                "arquivos do box nao encontrados em " + DIR_BOX, 404)

        # ---- material_modify_info.json (overlay que a tela escreve) ----
        modify = _le(ARQ_MODIFY)
        try:
            slot_m = modify["Material"][box_i]["list"][slot_i]
        except (KeyError, IndexError):
            raise self.server.error("estrutura inesperada no material_modify_info", 500)
        slot_m.update({
            "editStatus": 1, "filamentId": fil_id, "color": cor_fw,
            "brand": marca, "name": nome, "materialType": mat,
            "minTemp": tmin, "maxTemp": tmax,
        })
        if pressao:
            slot_m["pressure"] = pressao
        elif not str(slot_m.get("pressure", "")).strip():
            slot_m["pressure"] = "0.04"
        if not str(slot_m.get("remainLen", "")).strip():
            slot_m["remainLen"] = "100"
        if not str(slot_m.get("maxVSpeed", "")).strip():
            slot_m["maxVSpeed"] = "0"
        _grava(ARQ_MODIFY, modify)

        # ---- material_box_info.json (estado corrente) — espelha a tela ----
        boxinfo = _le(ARQ_BOX)
        try:
            caixas = boxinfo["Material"]["info"]
            alvo = next(c for c in caixas if c.get("boxID") == "T" + tnn[1])
            slot_b = alvo["list"][slot_i]
        except (KeyError, IndexError, StopIteration):
            slot_b = None  # caixa ausente no estado atual: overlay ja basta
        if slot_b is not None:
            slot_b.update({
                "editStatus": 1, "filamentId": fil_id, "color": cor_fw,
                "brand": marca, "name": nome, "materialType": mat,
                "minTemp": tmin, "maxTemp": tmax,
            })
            if pressao:
                slot_b["pressure"] = pressao
            _grava(ARQ_BOX, boxinfo)

        return {"ok": True, "tnn": tnn, "color": cor_fw, "materialType": mat,
                "name": nome, "gravado_box_info": slot_b is not None}


def load_component(config: ConfigHelper) -> JoelmaCfsEdit:
    return JoelmaCfsEdit(config)
