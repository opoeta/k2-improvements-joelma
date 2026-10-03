#!/bin/ash
# Backend do "Parar Homing": patcha o webhooks.py (endpoint force_stop_homing)
# pra abortar um homing errado sem e-stop total. Idempotente/fail-open: recusa
# sem alterar se o anchor nao existir. NAO-FATAL: loga e segue.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
TARGET=~/klipper/klippy/webhooks.py
set +e
python3 ${SCRIPT_DIR}/patch_webhooks.py "$TARGET"
RC=$?
set -e
if [ "$RC" -eq 0 ] || [ "$RC" -eq 2 ]; then
    rm -f ~/klipper/klippy/webhooks.pyc ~/klipper/klippy/__pycache__/webhooks.*.pyc 2>/dev/null || true
    echo "I: abort_homing aplicado (RC=$RC) - reiniciando klipper"
    /etc/init.d/klipper restart
else
    echo "W: abort_homing NAO aplicado (RC=$RC) - webhooks.py inalterado, seguindo"
fi
exit 0
