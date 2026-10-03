#!/bin/ash
# OPT-IN (fora do install padrao): rede de seguranca do SAVE_CONFIG. Substitui o
# configfile.py do Klipper (versao Rcpilot33; base 558 = a do 1.1.7.0 + 86 da
# feature) + helper. Apos SAVE_CONFIG faz UM FIRMWARE_RESTART protegido e, se o
# motor nao inicializar, reverte. SUBSTITUI CORE CRITICO DE BOOT -> backup +
# rollback no README. Rode consciente e confirme que o Klipper sobe depois.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
KLIPPY=~/klipper/klippy
TARGET=${KLIPPY}/configfile.py
HELPER=${KLIPPY}/k2_save_config_restart.sh
TS=$(date +%Y%m%d-%H%M%S)
if [ -f ${TARGET} ] && [ ! -L ${TARGET} ]; then
    cp -p ${TARGET} ${TARGET}.orig.${TS}
    echo "I: backup em ${TARGET}.orig.${TS}"
fi
rm -f ${TARGET} ${KLIPPY}/configfile.pyc ${KLIPPY}/__pycache__/configfile.*.pyc 2>/dev/null || true
ln -sf ${SCRIPT_DIR}/configfile.py ${TARGET}
ln -sf ${SCRIPT_DIR}/k2_save_config_restart.sh ${HELPER}
chmod +x ${SCRIPT_DIR}/k2_save_config_restart.sh
/etc/init.d/klipper restart
echo "I: save-config-restart instalado (OPT-IN). Se o Klipper NAO subir, rollback no README."
