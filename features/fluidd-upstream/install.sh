#!/bin/ash
# Instala a ULTIMA release oficial do Fluidd (fluidd-core/fluidd) por cima do
# build cortado da Creality em /usr/share/fluidd (porta 4408).
#
# - Idempotente: compara o release_info.json local com a tag mais recente no
#   GitHub e so baixa se houver versao nova.
# - Backup do build da Creality em /usr/share/fluidd_backup (so na 1a vez).
#   Rollback: rm -rf /usr/share/fluidd && cp -r /usr/share/fluidd_backup /usr/share/fluidd
# - Preserva os extras da Joelma: camera.html/snapshot.html (do moonraker-upgrade)
#   e reinstala a Central de Calibracao (nivela_web) por cima do fluidd novo.
#
# O firmware stock nao tem curl/wget: download via python3 (urllib), mesmo
# padrao do bootstrap-joelma.sh.

set -e

SCRIPT_DIR=$(readlink -f $(dirname $0))
DEST=/usr/share/fluidd
BKP=/usr/share/fluidd_backup
ZIP=/mnt/UDISK/fluidd-latest.zip
TMP=/mnt/UDISK/.fluidd-new
API="https://api.github.com/repos/fluidd-core/fluidd/releases/latest"
URL="https://github.com/fluidd-core/fluidd/releases/latest/download/fluidd.zip"

# ---------- versao remota (tag) x local (release_info.json do fluidd) ----------
REMOTA=$(python3 -c "import json,ssl,urllib.request;ctx=ssl._create_unverified_context();print(json.load(urllib.request.urlopen('${API}',context=ctx,timeout=30))['tag_name'])" 2>/dev/null || true)
LOCAL=""
if [ -f ${DEST}/release_info.json ]; then
    LOCAL=$(python3 -c "import json;print(json.load(open('${DEST}/release_info.json')).get('version',''))" 2>/dev/null || true)
fi
echo "I: fluidd local: ${LOCAL:-nenhum (build da Creality)} | ultima release: ${REMOTA:-?}"
if [ -n "$REMOTA" ] && [ "$REMOTA" = "$LOCAL" ]; then
    echo "I: fluidd ja esta na ultima versao - nada a fazer"
    exit 0
fi

# ---------- download ----------
echo "I: baixando fluidd.zip (${REMOTA:-latest})"
python3 - "$URL" "$ZIP" << 'PYEOF'
import socket, ssl, sys, urllib.request
socket.setdefaulttimeout(120)
url, dest = sys.argv[1], sys.argv[2]
try:
    urllib.request.urlretrieve(url, dest)
except Exception:
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=ctx) as r, open(dest, "wb") as f:
        f.write(r.read())
PYEOF

# ---------- extrai num diretorio temporario e valida antes de trocar ----------
rm -rf ${TMP}
mkdir -p ${TMP}
python3 -c "import shutil; shutil.unpack_archive('${ZIP}', '${TMP}', 'zip')"
if [ ! -f ${TMP}/index.html ]; then
    echo "E: fluidd.zip inesperado (sem index.html) - abortando sem tocar no atual"
    rm -rf ${TMP} ${ZIP}
    exit 1
fi

# ---------- backup do build da Creality (so na 1a vez) e troca ----------
if [ ! -e ${BKP} ]; then
    echo "I: backup do fluidd da Creality em ${BKP}"
    cp -r ${DEST} ${BKP}
fi
rm -rf ${DEST}
mv ${TMP} ${DEST}
rm -f ${ZIP}

# ---------- repoe os extras da Joelma por cima do fluidd novo ----------
for f in camera.html snapshot.html; do
    [ -f ${BKP}/$f ] && cp ${BKP}/$f ${DEST}/$f && echo "I: ${f} preservado"
done
sh ${SCRIPT_DIR}/../nivela_web/install.sh

echo "I: fluidd ${REMOTA:-novo} instalado em ${DEST} - http://IP:4408 (Ctrl+F5)"
