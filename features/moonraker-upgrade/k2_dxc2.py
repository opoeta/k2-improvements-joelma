# k2_dxc2.py - componente Moonraker que ATIVA/DESATIVA o perfil DXC2 e edita
# as chaves de calibracao no [box] do box.cfg, SEMPRE com backup. Faz parte do
# fork k2-improvements.
#
# Mecanismo (o [box] e secao unica no box.cfg, nao da pra sobrepor de outro
# arquivo, entao editamos o box.cfg em si):
#   - ATIVAR : snapshot dos valores atuais (1a vez) -> grava perfil DXC2 ->
#              inclui custom/dxc2.cfg no custom/main.cfg.
#   - DESATIVAR: restaura o snapshot -> remove o include do dxc2.cfg.
#   - SET    : grava UMA chave da whitelist (calibracao fina).
# Toda escrita e atomica (tmp + replace) e precedida de backup timestampado.
# O FIRMWARE_RESTART NAO e disparado aqui: o painel da Central chama
# /printer/firmware_restart depois do POST (um unico dono do efeito).
#
# Endpoints:
#   GET  /server/k2/dxc2  -> {active, values:{...}, has_snapshot}
#   POST /server/k2/dxc2  body:
#        {"action":"enable"}                      ativa o perfil DXC2
#        {"action":"disable"}                     volta ao stock (snapshot)
#        {"action":"set","key":"Tn_retrude","value":"-18"}   grava 1 chave
from __future__ import annotations

import json
import os
import re
import shutil
import time
from typing import TYPE_CHECKING, Any, Dict, List

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest

CFG_DIR = "/mnt/UDISK/printer_data/config"
BOX_CFG = os.path.join(CFG_DIR, "box.cfg")
MAIN_CFG = os.path.join(CFG_DIR, "custom", "main.cfg")
SNAPSHOT = os.path.join(CFG_DIR, ".k2_dxc2_stock.json")
INCLUDE_LINE = "[include dxc2.cfg]"

# chaves do [box] que o toggle/edicao gerenciam (nada fora disto e tocado)
WHITELIST: List[str] = [
    "Tn_retrude", "buffer_empty_len",
    "check_cut_pos_x_max", "check_cut_pos_x_min", "Tn_extrude_temp",
]
# perfil DXC2 (referencia Tinman; ajuste fino ao vivo depois). So as chaves aqui
# sao trocadas no ATIVAR; o resto do [box] fica intacto.
DXC2_PROFILE: Dict[str, str] = {
    "Tn_retrude": "-18",
    "buffer_empty_len": "23.25",
    "check_cut_pos_x_max": "-5.0",
}


def _ler_valores(conteudo: str) -> Dict[str, str]:
    # le o valor atual de cada chave da whitelist no [box] (ignora linha
    # comentada com '#' no inicio). Preserva o valor cru (sem o comentario).
    out: Dict[str, str] = {}
    for k in WHITELIST:
        m = re.search(r"(?m)^[ \t]*%s[ \t]*:[ \t]*(\S+)" % re.escape(k), conteudo)
        if m:
            out[k] = m.group(1)
    return out


def _grava_chaves(conteudo: str, updates: Dict[str, str]) -> str:
    # substitui o VALOR de cada chave existente preservando indentacao e o
    # comentario na mesma linha. Chave ausente e ignorada (nao inventa linha).
    for k, v in updates.items():
        padrao = re.compile(
            r"(?m)^([ \t]*%s[ \t]*:[ \t]*)(\S+)([ \t]*)(#.*)?$" % re.escape(k))

        def _sub(m: "re.Match[str]") -> str:
            comentario = m.group(4) or ""
            espaco = m.group(3) if comentario else ""
            return "%s%s%s%s" % (m.group(1), v, espaco, comentario)

        conteudo = padrao.sub(_sub, conteudo, count=1)
    return conteudo


def _backup(caminho: str) -> str:
    bak = "%s.bak.%s" % (caminho, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(caminho, bak)
    return bak


def _grava_atomico(caminho: str, conteudo: str) -> None:
    tmp = caminho + ".tmp"
    with open(tmp, "w") as f:
        f.write(conteudo)
    os.replace(tmp, caminho)


def _ativo() -> bool:
    try:
        with open(MAIN_CFG, "r") as f:
            return any(l.strip() == INCLUDE_LINE for l in f)
    except OSError:
        return False


def _set_include(incluir: bool) -> None:
    try:
        with open(MAIN_CFG, "r") as f:
            linhas = f.read().splitlines()
    except OSError:
        linhas = []
    tem = any(l.strip() == INCLUDE_LINE for l in linhas)
    if incluir and not tem:
        linhas.append(INCLUDE_LINE)
        _grava_atomico(MAIN_CFG, "\n".join(linhas) + "\n")
    elif not incluir and tem:
        linhas = [l for l in linhas if l.strip() != INCLUDE_LINE]
        _grava_atomico(MAIN_CFG, "\n".join(linhas) + ("\n" if linhas else ""))


class K2Dxc2:
    def __init__(self, config: "ConfigHelper") -> None:
        self.server = config.get_server()
        self.server.register_endpoint(
            "/server/k2/dxc2",
            RequestType.GET | RequestType.POST,
            self._handle,
        )

    async def _handle(self, web_request: "WebRequest") -> Dict[str, Any]:
        if web_request.get_request_type() == RequestType.GET:
            conteudo = ""
            try:
                with open(BOX_CFG, "r") as f:
                    conteudo = f.read()
            except OSError:
                return {"ok": False, "erro": "box.cfg nao encontrado",
                        "active": False, "values": {}, "has_snapshot": False}
            return {"ok": True, "active": _ativo(),
                    "values": _ler_valores(conteudo),
                    "has_snapshot": os.path.isfile(SNAPSHOT)}
        acao = web_request.get_str("action", "").strip().lower()
        if acao == "enable":
            return self._enable()
        if acao == "disable":
            return self._disable()
        if acao == "set":
            return self._set(web_request)
        raise self.server.error("action invalida (enable|disable|set)", 400)

    def _enable(self) -> Dict[str, Any]:
        if not os.path.isfile(BOX_CFG):
            raise self.server.error("box.cfg nao encontrado", 404)
        with open(BOX_CFG, "r") as f:
            conteudo = f.read()
        # snapshot dos valores stock (so na 1a ativacao, pra restaurar os REAIS)
        if not os.path.isfile(SNAPSHOT):
            _grava_atomico(SNAPSHOT, json.dumps(_ler_valores(conteudo), indent=2))
        bak = _backup(BOX_CFG)
        _grava_atomico(BOX_CFG, _grava_chaves(conteudo, DXC2_PROFILE))
        _set_include(True)
        return {"ok": True, "active": True, "backup": bak,
                "aplicado": DXC2_PROFILE,
                "aviso": "reinicie o firmware para aplicar"}

    def _disable(self) -> Dict[str, Any]:
        if not os.path.isfile(BOX_CFG):
            raise self.server.error("box.cfg nao encontrado", 404)
        restaurar: Dict[str, str] = {}
        if os.path.isfile(SNAPSHOT):
            try:
                with open(SNAPSHOT, "r") as f:
                    restaurar = {k: str(v) for k, v in json.load(f).items()
                                 if k in WHITELIST}
            except (OSError, ValueError):
                restaurar = {}
        bak = None
        if restaurar:
            with open(BOX_CFG, "r") as f:
                conteudo = f.read()
            bak = _backup(BOX_CFG)
            _grava_atomico(BOX_CFG, _grava_chaves(conteudo, restaurar))
            try:
                os.remove(SNAPSHOT)
            except OSError:
                pass
        _set_include(False)
        return {"ok": True, "active": False, "backup": bak,
                "restaurado": restaurar,
                "aviso": "reinicie o firmware para aplicar"}

    def _set(self, web_request: "WebRequest") -> Dict[str, Any]:
        key = web_request.get_str("key", "").strip()
        value = web_request.get_str("value", "").strip()
        if key not in WHITELIST:
            raise self.server.error("key fora da whitelist", 400)
        if not re.match(r"^-?\d+(\.\d+)?$", value):
            raise self.server.error("value invalido (numero)", 400)
        if not os.path.isfile(BOX_CFG):
            raise self.server.error("box.cfg nao encontrado", 404)
        with open(BOX_CFG, "r") as f:
            conteudo = f.read()
        if key not in _ler_valores(conteudo):
            raise self.server.error("chave %s nao existe no [box]" % key, 404)
        bak = _backup(BOX_CFG)
        _grava_atomico(BOX_CFG, _grava_chaves(conteudo, {key: value}))
        return {"ok": True, "key": key, "value": value, "backup": bak,
                "aviso": "reinicie o firmware para aplicar"}


def load_component(config: "ConfigHelper") -> K2Dxc2:
    return K2Dxc2(config)
