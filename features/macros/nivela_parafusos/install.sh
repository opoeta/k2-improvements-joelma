#!/bin/ash

set -e

SCRIPT_DIR="$(readlink -f $(dirname $0))"

test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom

# add the main.cfg to printer.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
# add the nivela_parafusos.cfg
ln -sf ${SCRIPT_DIR}/nivela_parafusos.cfg \
    ~/printer_data/config/custom/nivela_parafusos.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg nivela_parafusos.cfg

/etc/init.d/klipper restart
