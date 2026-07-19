#!/bin/ash
# Acelera a calibracao pre-impressao (mesh + z_tilt) sem tirar pontos: sobe o
# 'speed' de [bed_mesh] e [z_tilt] no printer.cfg stock. Idempotente + backup.
# Ver features/probe-speed/tune.py pra a logica e a seguranca.
# tune.py: rc 10 = mudou (reinicia), 0 = nada a fazer, 1 = erro.

SCRIPT_DIR=$(readlink -f $(dirname $0))
CFG=~/printer_data/config/printer.cfg

python "${SCRIPT_DIR}/tune.py" "${CFG}"
RC=$?

if [ "$RC" = "10" ]; then
    /etc/init.d/klipper restart
    echo "I: mesh/z_tilt mais rapidos - Klipper reiniciado"
elif [ "$RC" != "0" ]; then
    echo "E: probe-speed/tune.py falhou (rc=${RC}) - printer.cfg intacto"
    exit 1
fi
