#!/bin/ash
# Torna o START_PRINT (e o M191 aninhado) CANCELAVEL quando o firmware expoe a API
# de cancel da Creality (>=1.1.5.5). O modulo se auto-ativa no boot so se a API
# existir; senao fica inerte. Guarda aqui: so instala se o gcode.py tiver a API,
# e remove include antigo pra nao deixar referencia morta (que trava o boot).
# Portado de Rcpilot33.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
GCODE_PY=~/klipper/klippy/gcode.py
CUSTOM=~/printer_data/config/custom
test -d "$CUSTOM" || mkdir -p "$CUSTOM"
if ! grep -q 'check_cancel=' "$GCODE_PY" 2>/dev/null || ! grep -q 'cancel_pending' "$GCODE_PY" 2>/dev/null; then
    echo "I: fast_stop NAO instalado - API de cancel da Creality ausente neste firmware"
    rm -f ~/klipper/klippy/extras/k2_start_print_fast_stop.py \
          "$CUSTOM/k2_start_print_fast_stop.cfg" 2>/dev/null || true
    # remove include morto de main.cfg (senao o Klipper nao sobe)
    [ -f "$CUSTOM/main.cfg" ] && sed -i '/k2_start_print_fast_stop\.cfg/d' "$CUSTOM/main.cfg" 2>/dev/null || true
    exit 0
fi
rm -f ~/klipper/klippy/extras/k2_start_print_fast_stop.pyc \
      ~/klipper/klippy/extras/__pycache__/k2_start_print_fast_stop.*.pyc 2>/dev/null || true
ln -sf ${SCRIPT_DIR}/k2_start_print_fast_stop.py  ~/klipper/klippy/extras/k2_start_print_fast_stop.py
ln -sf ${SCRIPT_DIR}/k2_start_print_fast_stop.cfg "$CUSTOM/k2_start_print_fast_stop.cfg"
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    "$CUSTOM/main.cfg" k2_start_print_fast_stop.cfg
echo "I: fast_stop instalado (START_PRINT cancelavel)"
/etc/init.d/klipper restart
