#!/bin/ash
# KAMP LINE_PURGE - versao Joelma (fw 1.1.6.x):
# - baixa o KAMP como tarball via python3 (o stock nao tem git)
# - guarda em /mnt/UDISK/kamp (fora do overlay pequeno do rootfs)
# - sem prompt interativo (retracao e por filamento no slicer)
# - [exclude_object]: o printer.cfg stock do 1.1.6.x ja traz a secao

set -e

SCRIPT_DIR="$(readlink -f $(dirname $0))"
KAMP_DIR=/mnt/UDISK/kamp
SRC=/mnt/UDISK/.kamp-src
TGZ=/mnt/UDISK/kamp.tar.gz
URL="https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging/archive/refs/heads/main.tar.gz"

test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom

# 1. Baixa e extrai apenas o Line_Purge.cfg
echo "I: baixando KAMP (tarball, sem git)"
python3 - "$URL" "$TGZ" << 'PYEOF'
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
mkdir -p ${SRC} ${KAMP_DIR}
tar xzf ${TGZ} -C ${SRC}
cp -f ${SRC}/*/Configuration/Line_Purge.cfg ${KAMP_DIR}/Line_Purge.cfg
rm -rf ${TGZ} ${SRC}

# 2. Symlink do Line_Purge + copia dos settings ajustaveis
ln -sfn ${KAMP_DIR}/Line_Purge.cfg ~/printer_data/config/custom/Line_Purge.cfg
cp -f ${SCRIPT_DIR}/kamp_settings.cfg ~/printer_data/config/custom/kamp_settings.cfg

# 3. [exclude_object] apenas se nao existir em nenhum cfg
if ! grep -rEhq '^\[exclude_object\]' ~/printer_data/config/ 2>/dev/null; then
    cp -f ${SCRIPT_DIR}/exclude_object.cfg ~/printer_data/config/custom/exclude_object.cfg
    python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
        ~/printer_data/config/custom/main.cfg exclude_object.cfg
else
    echo "I: [exclude_object] ja existe no config stock - ok"
fi

# 4. Includes
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg kamp_settings.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg Line_Purge.cfg

/etc/init.d/klipper restart
echo "I: KAMP LINE_PURGE instalado - ligue Label objects no slicer e troque a prime line por LINE_PURGE"
