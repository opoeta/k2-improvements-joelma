#!/bin/ash
# KAMP LINE_PURGE + ADAPTIVE MESHING - versao Joelma (fw 1.1.6.x):
# - Line_Purge.cfg e Adaptive_Meshing.cfg sao VENDORADOS neste diretorio
#   (upstream kyleisah/Klipper-Adaptive-Meshing-Purging @ b0dad8e), nada de
#   download em runtime: deploy deterministico e offline.
# - Adaptive_Meshing.cfg carrega o PATCH JOELMA: PROBE_COUNT travado na grade
#   do config (5x5). O blob prtouch_v3_wrapper da Creality estoura IndexError
#   (linha 1925 -> key60 -> shutdown) com contagem menor que a do config.
# - guarda em /mnt/UDISK/kamp (fora do overlay pequeno do rootfs)
# - sem prompt interativo (retracao e por filamento no slicer)
# - [exclude_object]: o printer.cfg stock do 1.1.6.x ja traz a secao

set -e

SCRIPT_DIR="$(readlink -f $(dirname $0))"
KAMP_DIR=/mnt/UDISK/kamp

test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom
mkdir -p ${KAMP_DIR}

# 1. Copia os cfgs vendorados (substitui o download antigo do tarball)
echo "I: instalando KAMP vendorado (Line_Purge + Adaptive_Meshing patched)"
cp -f ${SCRIPT_DIR}/Line_Purge.cfg ${KAMP_DIR}/Line_Purge.cfg
cp -f ${SCRIPT_DIR}/Adaptive_Meshing.cfg ${KAMP_DIR}/Adaptive_Meshing.cfg

# sanity: o patch anti-shutdown precisa estar presente no arquivo instalado
grep -q "PATCH JOELMA" ${KAMP_DIR}/Adaptive_Meshing.cfg || {
    echo "E: Adaptive_Meshing.cfg sem o PATCH JOELMA - abortando" >&2
    exit 1
}

# 2. Symlink dos cfgs + copia dos settings ajustaveis
ln -sfn ${KAMP_DIR}/Line_Purge.cfg ~/printer_data/config/custom/Line_Purge.cfg
ln -sfn ${KAMP_DIR}/Adaptive_Meshing.cfg ~/printer_data/config/custom/Adaptive_Meshing.cfg
cp -f ${SCRIPT_DIR}/kamp_settings.cfg ~/printer_data/config/custom/kamp_settings.cfg

# 3. [exclude_object] apenas se nao existir em nenhum cfg
if ! grep -rEhq '^\[exclude_object\]' ~/printer_data/config/ 2>/dev/null; then
    cp -f ${SCRIPT_DIR}/exclude_object.cfg ~/printer_data/config/custom/exclude_object.cfg
    python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
        ~/printer_data/config/custom/main.cfg exclude_object.cfg
else
    echo "I: [exclude_object] ja existe no config stock - ok"
fi

# 4. Includes
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg kamp_settings.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg Line_Purge.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg Adaptive_Meshing.cfg

/etc/init.d/klipper restart
echo "I: KAMP LINE_PURGE instalado - ligue Label objects no slicer e troque a prime line por LINE_PURGE"
