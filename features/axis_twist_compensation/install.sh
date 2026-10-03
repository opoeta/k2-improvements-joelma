#!/bin/ash
# OPT-IN (fora do install padrao): habilita o axis_twist_compensation.
# Substitui o probe.py do Klipper (versao Rcpilot33, que casa com a linhagem do
# 1.1.7.0: 514 vs stock 513) + patcha o prtouch_v3 (libera o alias axis_twist).
# BACKUP do probe.py original antes de trocar. Se a sondagem quebrar, rode o
# ROLLBACK (README). So substitui core -> rode consciente e teste o probe depois.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
EXTRAS=/usr/share/klipper/klippy/extras
TS=$(date +%Y%m%d-%H%M%S)
# backup do probe.py ORIGINAL (so se for arquivo real, nao symlink de reinstall)
if [ -f ${EXTRAS}/probe.py ] && [ ! -L ${EXTRAS}/probe.py ]; then
    cp -p ${EXTRAS}/probe.py ${EXTRAS}/probe.py.orig.${TS}
    echo "I: backup em ${EXTRAS}/probe.py.orig.${TS}"
fi
rm -f ${EXTRAS}/probe.py ${EXTRAS}/probe.pyc ${EXTRAS}/__pycache__/probe.*.pyc 2>/dev/null || true
# patch do prtouch_v3 (libera o alias axis_twist) - so se existir o .py (nao o .so)
if [ -e ${EXTRAS}/prtouch_v3.py ]; then
    python ${SCRIPT_DIR}/patch_prtouch_registration.py ${EXTRAS}/prtouch_v3.py || true
fi
ln -sf ${SCRIPT_DIR}/probe.py ${EXTRAS}/probe.py
ln -sf ${SCRIPT_DIR}/axis_twist_compensation.py ${EXTRAS}/axis_twist_compensation.py
test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom
ln -sf ${SCRIPT_DIR}/axis_twist_compensation.cfg ~/printer_data/config/custom/axis_twist_compensation.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py ~/printer_data/config/printer.cfg custom/main.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py ~/printer_data/config/custom/main.cfg axis_twist_compensation.cfg
/etc/init.d/klipper restart
echo "I: axis_twist_compensation instalado (OPT-IN). TESTE o probe/homing. Rollback no README."
