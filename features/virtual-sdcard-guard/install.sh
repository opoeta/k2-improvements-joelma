#!/bin/ash
# Corrige o bug da Creality que anexa o delimitador HTTP multipart no fim do
# gcode (-> "Unknown command" depois do print). Patcha virtual_sdcard.py IN PLACE
# (idempotente; recusa sem alterar se o anchor nao existir). Portado de Rcpilot33.
# Nao-fatal: se nao aplicar, loga e segue.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
TARGET=~/klipper/klippy/extras/virtual_sdcard.py
if [ ! -f "$TARGET" ]; then echo "W: virtual_sdcard.py nao encontrado em $TARGET - pulando"; exit 0; fi
set +e
python3 ${SCRIPT_DIR}/patch_virtual_sdcard.py "$TARGET"
RC=$?
set -e
if [ "$RC" -eq 0 ] || [ "$RC" -eq 2 ]; then
    rm -f "${TARGET}c" ~/klipper/klippy/extras/__pycache__/virtual_sdcard.*.pyc 2>/dev/null || true
    echo "I: virtual-sdcard-guard aplicado (RC=$RC) - reiniciando klipper"
    /etc/init.d/klipper restart
else
    echo "W: virtual-sdcard-guard NAO aplicado (RC=$RC) - virtual_sdcard.py inalterado, seguindo"
fi
exit 0
