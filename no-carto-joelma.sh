#!/bin/ash
# ============================================================
# Instalador k2-improvements SEM Cartographer - K2 Plus (Joelma)
# v2 - ADAPTADO PARA FIRMWARE 1.1.6.x
#
# No 1.1.6.x a Creality ja embute Moonraker (7125) e Fluidd
# (4408) de fabrica. Por isso esta versao NAO instala:
#   entware, better-root, better-init, moonraker, fluidd
# (redundantes ou conflitantes com os servicos stock).
#
# Instala apenas: screws_tilt_adjust + macros (start_print,
# bed_mesh/MESH_IF_NEEDED, M191, overrides).
# ============================================================

set -e

SCRIPT_DIR=$(readlink -f $(dirname ${0}))
CFG=/mnt/UDISK/printer_data/config

# ---------- 0. Sanidade: dependencias stock das macros ----------
echo "==> Verificando macros stock exigidas pelo START_PRINT..."
for M in BOX_START_PRINT BOX_NOZZLE_CLEAN BOX_GO_TO_EXTRUDE_POS z_tilt; do
    if ! grep -rq "$M" ${CFG}/*.cfg; then
        echo "E: '$M' nao encontrado nos cfg stock - firmware mudou algo."
        echo "   Abortando por seguranca. Mande esta saida pro Claude."
        exit 1
    fi
done
echo "    OK - BOX_* e z_tilt presentes"

# ---------- 1. Symlinks de compatibilidade ----------
# No 1.1.6.x /root vem vazio; os install.sh esperam ~/printer_data
# e ~/klipper (layout que o better-root criava nos firmwares antigos).
echo "==> Criando symlinks de compatibilidade em /root..."
[ -e /root/printer_data ] || ln -s /mnt/UDISK/printer_data /root/printer_data
[ -e /root/klipper ]      || ln -s /usr/share/klipper      /root/klipper
ls -la /root/

# ---------- 2. Features (cada install reinicia o klipper) ----------
run_step() {
    echo ""
    echo "============================================"
    echo "==> Instalando: ${1}"
    echo "============================================"
    sh ${SCRIPT_DIR}/${2}
}

run_step screws_tilt_adjust features/screws_tilt_adjust/install.sh
# acelera a viagem entre os pontos do mesh/z_tilt (bed_mesh 100->600, z_tilt
# 300->600) sem tirar pontos - patch idempotente no printer.cfg stock
run_step probe_speed        features/probe-speed/install.sh
run_step macros/bed_mesh    features/macros/bed_mesh/install.sh
run_step macros/m191        features/macros/m191/install.sh
run_step macros/start_print features/macros/start_print/install.sh
run_step macros/overrides   features/macros/overrides/install.sh
run_step macros/nivela      features/macros/nivela_parafusos/install.sh
# blindagem do bug key171/key60 (BOX_SET_PRE_LOADING com ADDR/NUM vazios)
run_step macros/box_guard   features/macros/box_guard/install.sh
# sync de filamentos CFS -> OrcaSlicer (objeto [mmu] simulado, lido via Moonraker)
run_step macros/orca_sync   features/macros/orca-filament-sync/install.sh
# camera legada (registro webrtc-creality no DB) - substituida pelo
# moonraker-upgrade, que traz a [webcam Default] via iframe
#run_step camera             features/camera/install.sh
run_step moonraker_upgrade  features/moonraker-upgrade/install.sh
# ultima release oficial do Fluidd (fluidd-core) no lugar do build da Creality;
# ja reinstala a nivela_web por cima — o run_step seguinte fica como garantia
run_step fluidd_upstream    features/fluidd-upstream/install.sh
run_step nivela_web         features/nivela_web/install.sh

# ---------- OPCIONAIS (descomente para instalar) ----------
# Purga adaptativa KAMP (LINE_PURGE) - exige Label objects no slicer
run_step kamp               features/kamp-adaptive-purge/install.sh

echo ""
echo "============================================"
echo " Instalacao concluida! (firmware 1.1.6.x)"
echo " Fluidd stock: http://$(ip route get 1 2>/dev/null | awk '{print $7; exit}'):4408"
echo ""
echo " Instalado: SCREWS_TILT_CALCULATE, START_PRINT,"
echo " MESH_IF_NEEDED, M191, overrides (forced_leveling off)"
echo ""
echo " PROXIMO PASSO: gcode inicial no slicer:"
echo " START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] CHAMBER_TEMP=[overall_chamber_temperature] MATERIAL={filament_type[initial_tool]} CURR_BED_TYPE=\"{curr_bed_type}\" ADAPTIVE=1"
echo "============================================"
