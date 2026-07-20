#!/bin/ash

set -e

SCRIPT_DIR="$(readlink -f $(dirname $0))"

test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom

# add the main.cfg to printer.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
# add the start_print.cfg
ln -sf ${SCRIPT_DIR}/start_print.cfg \
    ~/printer_data/config/custom/start_print.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg start_print.cfg

# [save_variables] para o Z-offset persistente por placa+material (SAVE_VARIABLE).
# Guarda anti-duplicata: secao [save_variables] repetida mata o Klipper no boot,
# entao so inclui se nenhum outro cfg ja a define.
# - find -L: os cfg instalados sao SYMLINKS (ln -sf) e o grep -r do GNU nao le
#   symlink em travessia (o do busybox le) - find -L cobre os dois mundos.
# - Lista QUEM define (visibilidade contra falso positivo de backup/cfg morto).
# - Se o existente aponta pra /tmp (tmpfs, ex. motor-state-guard), ABORTA alto:
#   os offsets salvos morreriam a cada desligamento - o oposto do prometido.
SV_FILES=""
for f in $(find -L ~/printer_data/config -type f -name '*.cfg' 2>/dev/null); do
    grep -qE '^\[save_variables\]' "$f" 2>/dev/null && SV_FILES="$SV_FILES $f" || true
done
if [ -n "$SV_FILES" ]; then
    echo "I: [save_variables] ja definido em:$SV_FILES"
    if grep -hE '^[[:space:]]*filename' $SV_FILES 2>/dev/null | grep -q '/tmp'; then
        echo "E: o [save_variables] existente aponta pra /tmp (tmpfs) - os offsets"
        echo "E: por placa+material NAO sobreviveriam ao desligar a impressora."
        echo "E: Aponte o filename pra /mnt/UDISK/printer_data/config/joelma_vars.cfg"
        echo "E: (ou remova a secao duplicada) e rode o update de novo."
        exit 1
    fi
    echo "I: o existente e persistente - SAVE_VARIABLE vai usar ele, nada a fazer"
else
    ln -sf ${SCRIPT_DIR}/save_vars.cfg \
        ~/printer_data/config/custom/save_vars.cfg
    python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
        ~/printer_data/config/custom/main.cfg save_vars.cfg
    echo "I: [save_variables] instalado (Z-offset por placa+material persistente)"
fi

/etc/init.d/klipper restart
