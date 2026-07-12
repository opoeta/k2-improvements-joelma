#!/bin/ash
# Instala a blindagem do BOX_SET_PRE_LOADING (bug key171/key60 — CFS).
# Mesmo padrao das demais macros: symlink em custom/ + include + restart.

set -e

SCRIPT_DIR="$(readlink -f $(dirname $0))"

test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom

# add the main.cfg to printer.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
# add the box_guard.cfg
ln -sf ${SCRIPT_DIR}/box_guard.cfg \
    ~/printer_data/config/custom/box_guard.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg box_guard.cfg

/etc/init.d/klipper restart
