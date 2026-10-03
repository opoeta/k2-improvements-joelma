#!/bin/ash
# Guarda anti-arrasto do bico no probe stock (PR Touch): enrola _HOME_Z/SAFE_MOVE_Z
# e recua a mesa ate clearance_z antes do 1o movimento XY, evitando que um contato
# precoce do PR Touch vire arrasto do bico pela mesa. Ativo so com prtouch_v3 e sem
# Cartographer (o modulo se auto-desliga nos outros casos). Portado de Rcpilot33.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom
rm -f ~/klipper/klippy/extras/k2_prtouch_safe_xy.pyc \
      ~/klipper/klippy/extras/__pycache__/k2_prtouch_safe_xy.*.pyc 2>/dev/null || true
ln -sf ${SCRIPT_DIR}/k2_prtouch_safe_xy.py  ~/klipper/klippy/extras/k2_prtouch_safe_xy.py
ln -sf ${SCRIPT_DIR}/k2_prtouch_safe_xy.cfg ~/printer_data/config/custom/k2_prtouch_safe_xy.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg k2_prtouch_safe_xy.cfg
/etc/init.d/klipper restart
