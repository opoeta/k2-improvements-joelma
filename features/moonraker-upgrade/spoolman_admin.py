# spoolman_admin.py - componente Moonraker para configurar o servidor Spoolman
# pela interface web (sem editar arquivos) e descobrir servidores na rede local.
#
# Endpoints:
#   GET  /server/spoolman_admin/config  -> {server, sync_rate}
#   POST /server/spoolman_admin/config  -> grava [spoolman] server no conf e reinicia
#   GET  /server/spoolman_admin/scan    -> varre a subnet local por servidores Spoolman
#
# Faz parte do fork k2-improvements-joelma. Reinstalado pela feature moonraker-upgrade.
from __future__ import annotations
import asyncio
import logging
import re
import os
import json
import socket
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..common import RequestType

if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from ..common import WebRequest

CONF_PATH = "/usr/share/moonraker/moonraker.conf"
# portas comuns onde o Spoolman costuma ser exposto (docker mapeia 8000 -> varias)
PORTAS_PADRAO = [7912, 8000, 8080, 7913]


class SpoolmanAdmin:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.conf_path = config.get("conf_path", CONF_PATH)
        self.server.register_endpoint(
            "/server/spoolman_admin/config",
            RequestType.GET | RequestType.POST,
            self._handle_config,
        )
        self.server.register_endpoint(
            "/server/spoolman_admin/scan",
            RequestType.GET,
            self._handle_scan,
        )
        logging.info("spoolman_admin: endpoints registrados")

    # ---------- config: le/grava a URL do servidor no moonraker.conf ----------
    def _ler_conf(self) -> Dict[str, Any]:
        server = None
        sync_rate = None
        try:
            with open(self.conf_path, "r") as f:
                txt = f.read()
        except Exception:
            return {"server": None, "sync_rate": None, "configurado": False}
        # extrai a secao [spoolman]
        m = re.search(r"^\[spoolman\]\s*$(.*?)(?=^\[|\Z)", txt,
                      re.MULTILINE | re.DOTALL)
        if m:
            bloco = m.group(1)
            ms = re.search(r"^\s*server:\s*(\S+)\s*$", bloco, re.MULTILINE)
            if ms:
                server = ms.group(1).strip()
            mr = re.search(r"^\s*sync_rate:\s*(\d+)\s*$", bloco, re.MULTILINE)
            if mr:
                sync_rate = int(mr.group(1))
        return {"server": server, "sync_rate": sync_rate,
                "configurado": server is not None}

    def _gravar_conf(self, server: str, sync_rate: int) -> None:
        try:
            with open(self.conf_path, "r") as f:
                txt = f.read()
        except Exception:
            txt = ""
        bloco = "[spoolman]\nserver: %s\nsync_rate: %d\n" % (server, sync_rate)
        if re.search(r"^\[spoolman\]\s*$", txt, re.MULTILINE):
            # substitui a secao existente inteira
            txt = re.sub(r"^\[spoolman\]\s*$.*?(?=^\[|\Z)",
                         bloco + "\n", txt, count=1,
                         flags=re.MULTILINE | re.DOTALL)
        else:
            if txt and not txt.endswith("\n"):
                txt += "\n"
            txt += "\n" + bloco
        # backup antes de gravar
        try:
            with open(self.conf_path + ".bak-admin", "w") as f:
                pass
            import shutil
            shutil.copy(self.conf_path, self.conf_path + ".bak-admin")
        except Exception:
            pass
        with open(self.conf_path, "w") as f:
            f.write(txt)

    async def _handle_config(self, web_request: WebRequest) -> Dict[str, Any]:
        if web_request.get_request_type() == RequestType.POST:
            server = web_request.get_str("server").strip()
            sync_rate = web_request.get_int("sync_rate", 5)
            # normaliza: garante http:// e sem barra final
            if not re.match(r"^https?://", server):
                server = "http://" + server
            server = server.rstrip("/")
            if not re.match(r"^https?://[^/\s]+", server):
                raise self.server.error("URL invalida: %s" % server, 400)
            self._gravar_conf(server, sync_rate)
            # responde primeiro, reinicia depois (senao a resposta nao chega)
            self.server.restart(delay=1.5)
            return {"server": server, "sync_rate": sync_rate,
                    "gravado": True, "reiniciando": True}
        return self._ler_conf()

    # ---------- scan: descobre servidores Spoolman na rede local ----------
    def _ip_local(self) -> Optional[str]:
        # descobre o IP da interface principal sem depender de internet real
        for alvo in [("10.255.255.255", 1), ("8.8.8.8", 80)]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1)
                s.connect(alvo)
                ip = s.getsockname()[0]
                s.close()
                if ip and not ip.startswith("127."):
                    return ip
            except Exception:
                continue
        return None

    async def _testa_spoolman(self, ip: str, porta: int,
                              sem: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
        async with sem:
            # 1) porta aberta?
            try:
                fut = asyncio.open_connection(ip, porta)
                reader, writer = await asyncio.wait_for(fut, timeout=0.6)
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
            except Exception:
                return None
            # 2) responde a API do Spoolman? (HTTP GET /api/v1/info)
            try:
                fut = asyncio.open_connection(ip, porta)
                reader, writer = await asyncio.wait_for(fut, timeout=1.5)
                req = ("GET /api/v1/info HTTP/1.1\r\nHost: %s:%d\r\n"
                       "Connection: close\r\n\r\n" % (ip, porta))
                writer.write(req.encode())
                await writer.drain()
                data = await asyncio.wait_for(reader.read(2048), timeout=1.5)
                writer.close()
            except Exception:
                return None
            txt = data.decode("utf-8", "replace")
            # separa corpo do cabecalho HTTP
            corpo = txt.split("\r\n\r\n", 1)[-1]
            if '"version"' not in corpo:
                return None
            versao = None
            mv = re.search(r'"version"\s*:\s*"([^"]+)"', corpo)
            if mv:
                versao = mv.group(1)
            return {"ip": ip, "porta": porta,
                    "url": "http://%s:%d" % (ip, porta), "versao": versao}

    async def _handle_scan(self, web_request: WebRequest) -> Dict[str, Any]:
        base = web_request.get_str("subnet", None)   # ex "10.10.1"
        portas_arg = web_request.get_str("portas", None)
        if portas_arg:
            try:
                portas = [int(p) for p in portas_arg.split(",") if p.strip()]
            except Exception:
                portas = PORTAS_PADRAO
        else:
            portas = PORTAS_PADRAO
        if not base:
            ip = self._ip_local()
            if not ip:
                raise self.server.error(
                    "nao consegui detectar a subnet; informe manualmente", 400)
            base = ".".join(ip.split(".")[:3])
        base = base.rstrip(".")
        # varre base.1 .. base.254 nas portas escolhidas
        sem = asyncio.Semaphore(80)
        tarefas = []
        for host in range(1, 255):
            ip = "%s.%d" % (base, host)
            for porta in portas:
                tarefas.append(self._testa_spoolman(ip, porta, sem))
        resultados = await asyncio.gather(*tarefas, return_exceptions=True)
        achados = [r for r in resultados
                   if isinstance(r, dict) and r is not None]
        # ordena por IP
        achados.sort(key=lambda r: tuple(int(x) for x in r["ip"].split(".")))
        return {"subnet": base, "portas": portas,
                "encontrados": achados, "total": len(achados)}


def load_component(config: ConfigHelper) -> SpoolmanAdmin:
    return SpoolmanAdmin(config)
