#!/usr/bin/env python3
# Dump do WebSocket da porta 9999 da K2 (servico Creality) — diagnostico do
# sync de CFS do OrcaSlicer. O Orca (PR #13752) le os slots do CFS por essa
# porta, na mensagem "boxsInfo", esperando cor "#0RRGGBB" e type/vendor por
# slot; este script mostra o payload REAL que a impressora envia.
#
# Roda no PC (mesma rede da impressora). Alem de escutar, envia a MESMA
# requisicao que o OrcaSlicer usa no sync (segura, o Orca a faz o tempo todo):
#   {"method":"get","params":{"boxsInfo":1}}
#
#   python scripts\dump_cfs_9999.py            (padrao: 10.10.1.240, 20s)
#   python scripts\dump_cfs_9999.py 10.10.1.240 30
#
# So biblioteca padrao (sem pip install). Python 3.8+.

import base64
import json
import os
import socket
import struct
import sys
import time

IP = sys.argv[1] if len(sys.argv) > 1 else "10.10.1.240"
DUR = int(sys.argv[2]) if len(sys.argv) > 2 else 20

key = base64.b64encode(os.urandom(16)).decode()
req = (
    "GET / HTTP/1.1\r\n"
    "Host: %s:9999\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Key: %s\r\n"
    "Sec-WebSocket-Version: 13\r\n\r\n"
) % (IP, key)

s = socket.create_connection((IP, 9999), timeout=8)
s.sendall(req.encode())
buf = b""
while b"\r\n\r\n" not in buf:
    parte = s.recv(4096)
    if not parte:
        sys.exit("E: conexao fechada durante o handshake")
    buf += parte
head, _, dados = buf.partition(b"\r\n\r\n")
print(head.decode(errors="replace").splitlines()[0])  # esperado: HTTP/1.1 101


def envia(op, payload=b""):
    # frames cliente->servidor precisam de mascara (RFC 6455)
    m = os.urandom(4)
    hdr = bytes([0x80 | op, 0x80 | len(payload)]) + m
    s.sendall(hdr + bytes(b ^ m[i % 4] for i, b in enumerate(payload)))


def frames(dados):
    """Extrai frames completos; devolve (frames, resto_do_buffer)."""
    prontos = []
    while True:
        if len(dados) < 2:
            return prontos, dados
        b1, b2 = dados[0], dados[1]
        ln = b2 & 0x7F
        off = 2
        if ln == 126:
            if len(dados) < 4:
                return prontos, dados
            ln = struct.unpack(">H", dados[2:4])[0]
            off = 4
        elif ln == 127:
            if len(dados) < 10:
                return prontos, dados
            ln = struct.unpack(">Q", dados[2:10])[0]
            off = 10
        if b2 & 0x80:  # servidor mascarado (raro); pula a mascara
            off += 4
        if len(dados) < off + ln:
            return prontos, dados
        prontos.append((b1 & 0x0F, dados[off:off + ln]))
        dados = dados[off + ln:]


s.settimeout(2)
# pede o boxsInfo ativamente — mesma requisicao do OrcaSlicer (CrealityPrint.cpp)
envia_texto = lambda obj: envia(1, json.dumps(obj).encode())
envia_texto({"method": "get", "params": {"boxsInfo": 1}})

fim = time.time() + DUR
achou_box = False
while time.time() < fim:
    try:
        chunk = s.recv(65536)
        if not chunk:
            print("(servidor encerrou a conexao)")
            break
        dados += chunk
    except socket.timeout:
        continue
    prontos, dados = frames(dados)
    for op, payload in prontos:
        if op == 9:           # ping -> pong, senao o servidor derruba
            envia(10, payload)
            continue
        if op != 1:           # so frames de texto interessam
            continue
        txt = payload.decode(errors="replace")
        print("\n--- frame ---")
        try:
            j = json.loads(txt)
            print(json.dumps(j, indent=1, ensure_ascii=False)[:4000])
        except ValueError:
            print(txt[:2000])
        if "boxsInfo" in txt:
            achou_box = True
            print(">>> ESTE frame contem o boxsInfo que o Orca le ^^^")

print()
if achou_box:
    print("OK: boxsInfo capturado. Confira se cada slot traz color '#0RRGGBB'")
    print("e type/vendor preenchidos — slot sem type E vendor o Orca IGNORA,")
    print("e cor ausente/mal formatada vira branco (#FFFFFF).")
else:
    print("Nenhum boxsInfo em %ds. O servico da 9999 pode so responder a" % DUR)
    print("requisicao ativa (como o Orca faz) — mande esta saida pro Claude.")
