# k2_features.py - liga/desliga os RECURSOS AVANCADOS que trocam arquivo do
# Klipper (axis_twist, save-config-restart), direto pela Central, com status e
# backup. Zero SSH. Faz parte do fork k2-improvements-joelma.
#
# Como funciona: cada recurso e um conjunto de SYMLINKS (arquivo do repo ->
# destino no Klipper) + opcional include de cfg + opcional patch. Ativar faz
# BACKUP do original (<dest>.k2-orig, uma vez), aponta o symlink e reinicia
# o Klipper. Desativar restaura o backup e reinicia. O estado (ativo/inativo) e
# detectado pelo symlink -> seguro e idempotente. Mesmo que o configfile.py
# quebre o host do Klipper, o Moonraker continua e o DESATIVAR daqui recupera.
#
# Endpoints:
#   GET  /server/k2/features                      -> estado de cada recurso
#   POST /server/k2/features {feature, action}    action = enable|disable
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest

EXTRAS = "/usr/share/klipper/klippy/extras"
KLIPPY = "/usr/share/klipper/klippy"
MAIN_CFG = "/mnt/UDISK/printer_data/config/custom/main.cfg"
ORIG = ".k2-orig"

# Registro dos recursos toggleaveis. Caminhos de origem sao RELATIVOS ao repo.
FEATURES: Dict[str, Dict[str, Any]] = {
    "axis_twist": {
        "label": "Axis Twist Compensation",
        "desc": "Compensa drift de Z ao longo de X/Y (melhora a 1a camada).",
        "links": [
            ("features/axis_twist_compensation/probe.py", EXTRAS + "/probe.py"),
            ("features/axis_twist_compensation/axis_twist_compensation.py",
             EXTRAS + "/axis_twist_compensation.py"),
        ],
        "cfg": ("features/axis_twist_compensation/axis_twist_compensation.cfg",
                "axis_twist_compensation.cfg"),
        "patch": ("features/axis_twist_compensation/patch_prtouch_registration.py",
                  EXTRAS + "/prtouch_v3.py"),
    },
    "save_config_restart": {
        "label": "SAVE_CONFIG protegido",
        "desc": "Restart protegido apos SAVE_CONFIG (reverte se o motor nao subir).",
        "links": [
            ("features/save-config-restart/configfile.py", KLIPPY + "/configfile.py"),
            ("features/save-config-restart/k2_save_config_restart.sh",
             KLIPPY + "/k2_save_config_restart.sh"),
        ],
        "cfg": None,
        "patch": None,
    },
}


def _is_active(repo: str, feat: Dict[str, Any]) -> bool:
    # ativo = o 1o destino e symlink apontando pra dentro do repo
    try:
        dest = feat["links"][0][1]
        return os.path.islink(dest) and os.path.realpath(dest).startswith(repo)
    except OSError:
        return False


def _backup_once(dest: str) -> None:
    # guarda o original UMA vez (so se for arquivo real, nao symlink)
    bak = dest + ORIG
    if os.path.exists(dest) and not os.path.islink(dest) and not os.path.exists(bak):
        shutil.copy2(dest, bak)


def _restore(dest: str) -> None:
    bak = dest + ORIG
    if os.path.islink(dest):
        try:
            os.remove(dest)
        except OSError:
            pass
    if os.path.exists(bak):
        shutil.move(bak, dest)


def _rm_pyc(dest: str) -> None:
    base = os.path.basename(dest)
    if base.endswith(".py"):
        for p in (dest + "c", os.path.join(os.path.dirname(dest),
                  "__pycache__")):
            try:
                if p.endswith("__pycache__") and os.path.isdir(p):
                    for f in os.listdir(p):
                        if f.startswith(base[:-3] + "."):
                            os.remove(os.path.join(p, f))
                elif os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass


def _include(name: str, add: bool) -> None:
    line = "[include %s]" % name
    try:
        with open(MAIN_CFG, "r") as f:
            linhas = f.read().splitlines()
    except OSError:
        linhas = []
    tem = any(l.strip() == line for l in linhas)
    if add and not tem:
        linhas.append(line)
    elif not add and tem:
        linhas = [l for l in linhas if l.strip() != line]
    else:
        return
    tmp = MAIN_CFG + ".tmp"
    with open(tmp, "w") as f:
        f.write("\n".join(linhas) + ("\n" if linhas else ""))
    os.replace(tmp, MAIN_CFG)


class K2Features:
    def __init__(self, config: "ConfigHelper") -> None:
        self.server = config.get_server()
        self.repo = config.get("repo", "/mnt/UDISK/k2-improvements-joelma")
        self.server.register_endpoint(
            "/server/k2/features",
            RequestType.GET | RequestType.POST,
            self._handle,
        )

    async def _handle(self, web_request: "WebRequest") -> Dict[str, Any]:
        if web_request.get_request_type() == RequestType.GET:
            out: Dict[str, Any] = {}
            for key, feat in FEATURES.items():
                out[key] = {"label": feat["label"], "desc": feat["desc"],
                            "active": _is_active(self.repo, feat)}
            return {"ok": True, "repo": self.repo, "features": out}
        key = web_request.get_str("feature", "").strip()
        action = web_request.get_str("action", "").strip().lower()
        if key not in FEATURES:
            raise self.server.error("feature desconhecida", 400)
        if action not in ("enable", "disable"):
            raise self.server.error("action invalida (enable|disable)", 400)
        feat = FEATURES[key]
        try:
            if action == "enable":
                self._enable(feat)
            else:
                self._disable(feat)
        except Exception as e:
            logging.exception("k2_features %s %s", key, action)
            raise self.server.error("%s falhou: %s" % (action, e), 500)
        self._restart_klipper()
        return {"ok": True, "feature": key, "active": action == "enable",
                "aviso": "Klipper reiniciando"}

    def _src(self, rel: str) -> str:
        return os.path.join(self.repo, rel)

    def _enable(self, feat: Dict[str, Any]) -> None:
        for rel, dest in feat["links"]:
            src = self._src(rel)
            if not os.path.isfile(src):
                raise RuntimeError("arquivo do repo ausente: %s" % src)
            _backup_once(dest)
            _rm_pyc(dest)
            if os.path.islink(dest) or os.path.exists(dest):
                try:
                    os.remove(dest)
                except OSError:
                    pass
            os.symlink(src, dest)
        patch = feat.get("patch")
        if patch:
            prel, target = patch
            if os.path.isfile(target):
                _backup_once(target)
                subprocess.run(["python3", self._src(prel), target], check=False)
                _rm_pyc(target)
        cfg = feat.get("cfg")
        if cfg:
            crel, cname = cfg
            dest = os.path.join(os.path.dirname(MAIN_CFG), cname)
            if os.path.islink(dest) or os.path.exists(dest):
                try:
                    os.remove(dest)
                except OSError:
                    pass
            os.symlink(self._src(crel), dest)
            _include(cname, True)

    def _disable(self, feat: Dict[str, Any]) -> None:
        for rel, dest in feat["links"]:
            _rm_pyc(dest)
            _restore(dest)
        patch = feat.get("patch")
        if patch:
            _rm_pyc(patch[1])
            _restore(patch[1])
        cfg = feat.get("cfg")
        if cfg:
            _, cname = cfg
            _include(cname, False)
            dest = os.path.join(os.path.dirname(MAIN_CFG), cname)
            if os.path.islink(dest):
                try:
                    os.remove(dest)
                except OSError:
                    pass

    def _restart_klipper(self) -> None:
        # reinicia o HOST do Klipper (re-importa os .py trocados) em background,
        # pra nao segurar a resposta HTTP. O painel espera o Klipper voltar.
        def _do() -> None:
            try:
                subprocess.run(["/etc/init.d/klipper", "restart"], check=False)
            except Exception:
                logging.exception("k2_features: falha ao reiniciar klipper")
        try:
            self.server.get_event_loop().run_in_thread(_do)
        except Exception:
            _do()


def load_component(config: "ConfigHelper") -> K2Features:
    return K2Features(config)
