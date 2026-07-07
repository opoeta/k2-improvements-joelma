#!/bin/ash
# Registra a camera da K2 (webrtc_local porta 8000) no Moonraker.
# Idempotente: se a webcam "Joelma" ja existe, nao mexe - preserva
# ajustes feitos pela UI do Fluidd (flip, rotacao etc).
# O registro vive no banco do Moonraker; este passo garante que ele
# seja recriado apos factory reset ou troca de eMMC.

set -e

IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
if [ -z "$IP" ]; then
    echo "E: nao consegui detectar o IP da impressora"
    exit 1
fi

python3 - "$IP" << 'PYEOF'
import json, sys, urllib.request

ip = sys.argv[1]
base = "http://127.0.0.1:7125"
NOME = "Joelma"

lista = json.load(urllib.request.urlopen(base + "/server/webcams/list", timeout=10))
existentes = [w.get("name") for w in lista["result"]["webcams"]]
if NOME in existentes:
    print("camera '%s' ja registrada no Moonraker - mantendo como esta" % NOME)
    sys.exit(0)

body = json.dumps({
    "name": NOME,
    "service": "webrtc-creality",
    "enabled": True,
    "stream_url": "http://%s:8000/call/webrtc_local" % ip,
    "snapshot_url": "",
    "target_fps": 15,
    "aspect_ratio": "16:9",
}).encode()
req = urllib.request.Request(base + "/server/webcams/item", data=body,
                             headers={"Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=10)
print("camera '%s' registrada (webrtc-creality -> %s:8000)" % (NOME, ip))
PYEOF
