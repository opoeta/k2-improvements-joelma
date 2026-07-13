#!/bin/ash
# Moonraker upstream (via DnG-Crafts/K2-Camera): camera no Fluidd (iframe),
# componente spoolman, update_manager e API 1.4 - substitui o build cortado
# da Creality. Backup automatico em /usr/share/moonraker_backup.
# Reverter: parar moonraker, restaurar o backup, iniciar.

set -e
SRC=/mnt/UDISK/.k2cam-src
ZIP=/mnt/UDISK/k2cam.zip
URL="https://github.com/DnG-Crafts/K2-Camera/archive/refs/heads/main.zip"
CONF=/usr/share/moonraker/moonraker.conf
MUDOU=0

if ! grep -q "API_VERSION = (1, 4" /usr/share/moonraker/server.py 2>/dev/null; then
    echo "I: baixando K2-Camera (zip via python3)"
    python3 - "$URL" "$ZIP" << 'PYEOF'
import socket, ssl, sys, urllib.request
socket.setdefaulttimeout(60)
url, dest = sys.argv[1], sys.argv[2]
try:
    urllib.request.urlretrieve(url, dest)
except Exception:
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=ctx) as r, open(dest, "wb") as f:
        f.write(r.read())
PYEOF
    rm -rf ${SRC}
    mkdir -p ${SRC}
    python3 -c "import shutil; shutil.unpack_archive('${ZIP}', '${SRC}')"
    /etc/init.d/moonraker stop || true
    if [ ! -e /usr/share/moonraker_backup ]; then
        echo "I: backup do moonraker original em /usr/share/moonraker_backup"
        mv /usr/share/moonraker /usr/share/moonraker_backup
    fi
    rm -rf /usr/share/moonraker
    cp -r ${SRC}/K2-Camera-main/moonraker /usr/share/moonraker
    for f in camera.html snapshot.html index.html favicon.ico mylogo.png; do
        cp ${SRC}/K2-Camera-main/${f} /usr/share/frontend/${f}
    done
    cp ${SRC}/K2-Camera-main/camera.html   /usr/share/fluidd/camera.html
    cp ${SRC}/K2-Camera-main/snapshot.html /usr/share/fluidd/snapshot.html
    rm -rf ${ZIP} ${SRC}
    MUDOU=1
    echo "I: moonraker upstream instalado"
fi

# CORS por origem exata (wildcard de IP nao e permitido pelo moonraker 1.4)
sed -i '\|^  \*://10\.10\.1\.\*$|d' ${CONF}
if ! grep -q '10.10.1.240:4408' ${CONF}; then
    sed -i 's|^cors_domains:|cors_domains:\n  http://10.10.1.240:4408\n  http://10.10.1.240|' ${CONF}
    MUDOU=1
    echo "I: cors_domains com origens exatas da LAN"
fi

# Spoolman: componente cliente aponta para o servidor Docker na LAN
# (o servidor roda em 10.10.1.254:7912 - NAS). O proxy do Moonraker
# permite a Central falar a API sem CORS.
if ! grep -q '^\[spoolman\]' ${CONF}; then
    cat >> ${CONF} <<'SPOOL'

[spoolman]
server: http://10.10.1.254:7912
sync_rate: 5
SPOOL
    MUDOU=1
    echo "I: [spoolman] apontando para http://10.10.1.254:7912"
fi

# spoolman_admin: componente proprio que expoe endpoints para configurar o
# servidor Spoolman pela interface (sem editar arquivos) e escanear a rede.
# Copiado para components/ e ativado via secao [spoolman_admin] no conf.
FEAT_DIR=$(dirname "$0")
if [ -f "${FEAT_DIR}/spoolman_admin.py" ]; then
    cp "${FEAT_DIR}/spoolman_admin.py" /usr/share/moonraker/components/spoolman_admin.py
    echo "I: componente spoolman_admin.py copiado"
fi
if [ -f "${FEAT_DIR}/joelma_info.py" ]; then
    cp "${FEAT_DIR}/joelma_info.py" /usr/share/moonraker/components/joelma_info.py
    echo "I: componente joelma_info.py copiado"
fi
# joelma_resonances: expoe os CSVs de TEST_RESONANCES/SHAPER_CALIBRATE (/tmp)
# via REST para a Central desenhar os graficos de ressonancia no navegador.
if [ -f "${FEAT_DIR}/joelma_resonances.py" ]; then
    cp "${FEAT_DIR}/joelma_resonances.py" /usr/share/moonraker/components/joelma_resonances.py
    echo "I: componente joelma_resonances.py copiado"
fi
if ! grep -q '^\[joelma_resonances\]' ${CONF}; then
    cat >> ${CONF} <<'JRES'

[joelma_resonances]
JRES
    MUDOU=1
    echo "I: [joelma_resonances] ativado (graficos de ressonancia via REST)"
fi
# joelma_cfs_edit: edita material/cor de slot do CFS gravando nos JSONs do
# firmware (os mesmos que a tela usa) — sincroniza tela/Creality Print/Orca.
if [ -f "${FEAT_DIR}/joelma_cfs_edit.py" ]; then
    cp "${FEAT_DIR}/joelma_cfs_edit.py" /usr/share/moonraker/components/joelma_cfs_edit.py
    echo "I: componente joelma_cfs_edit.py copiado"
fi
if ! grep -q '^\[joelma_cfs_edit\]' ${CONF}; then
    cat >> ${CONF} <<'JCFS'

[joelma_cfs_edit]
JCFS
    MUDOU=1
    echo "I: [joelma_cfs_edit] ativado (edicao de slot gravada no firmware)"
fi
if ! grep -q '^\[joelma_info\]' ${CONF}; then
    cat >> ${CONF} <<'JINFO'

[joelma_info]
JINFO
    MUDOU=1
    echo "I: [joelma_info] ativado (versao do firmware da impressora)"
fi
if ! grep -q '^\[spoolman_admin\]' ${CONF}; then
    cat >> ${CONF} <<'SPADM'

[spoolman_admin]
SPADM
    MUDOU=1
    echo "I: [spoolman_admin] ativado (config + scan de rede pela interface)"
fi

if [ "$MUDOU" = "0" ]; then
    echo "I: moonraker upstream ja instalado e configurado - nada a fazer"
    exit 0
fi

/etc/init.d/moonraker restart || /etc/init.d/moonraker start

python3 << 'PYEOF'
import json, time, urllib.request
for _ in range(30):
    try:
        json.load(urllib.request.urlopen("http://127.0.0.1:7125/server/info", timeout=3))
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("E: moonraker nao subiu em 60s - rode o restore se necessario")
try:
    req = urllib.request.Request(
        "http://127.0.0.1:7125/server/webcams/item?name=Joelma", method="DELETE")
    urllib.request.urlopen(req, timeout=5)
    print("I: registro antigo 'Joelma' (webrtc-creality) removido do DB")
except Exception:
    pass
print("I: moonraker upstream ativo - camera no Fluidd via [webcam Default]")
PYEOF
