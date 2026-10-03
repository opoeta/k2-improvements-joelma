#!/bin/ash
# Scanner de footprint da 1a camada (extensao Klippy [prime_tower]).
# Le o gcode selecionado e calcula o retangulo real da camada 1 (modelo + brim +
# skirt + suportes + prime tower) -> mesh adaptativo / KAMP sabem onde a peca fica.
# Portado de Rcpilot33/k2-improvements (GPLv3). Idempotente.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom
rm -f ~/klipper/klippy/extras/prime_tower.pyc \
      ~/klipper/klippy/extras/__pycache__/prime_tower.*.pyc 2>/dev/null || true
ln -sf ${SCRIPT_DIR}/prime_tower.py  ~/klipper/klippy/extras/prime_tower.py
ln -sf ${SCRIPT_DIR}/prime_tower.cfg ~/printer_data/config/custom/prime_tower.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg prime_tower.cfg
/etc/init.d/klipper restart
