#!/bin/ash
# ============================================================
# Instalador k2-improvements SEM Cartographer - K2 Plus (Joelma)
# Baseado no no-carto.sh do upstream, corrigido:
#   - inclui entware e better-root-safe (faltavam no original;
#     moonraker/fluidd falham sem eles)
#   - usa better-root-safe (evita o bug "File exists" do moonraker)
#   - renova HOME apos better-root (o /etc/passwd muda mas o
#     shell logado mantem o HOME antigo em cache)
#   - start_print.cfg ja vem sem as chamadas CARTOGRAPHER_*
# Opcionais (abort_homing, skip-setup, kamp) ficam no final,
# desativados por padrao - descomente o que quiser.
# ============================================================

set -e

SCRIPT_DIR=$(readlink -f $(dirname ${0}))

# Garante que binarios do Entware fiquem no PATH durante a instalacao
export PATH="/opt/bin:/opt/sbin:/mnt/UDISK/bin:$PATH"

run_step() {
    NOME=${1}
    SCRIPT=${2}
    MARCA=/tmp/k2imp-$(echo ${NOME} | tr '/' '-')
    if [ -f ${MARCA} ]; then
        echo "==> ${NOME}: ja instalado nesta sessao, pulando"
        return 0
    fi
    echo ""
    echo "============================================"
    echo "==> Instalando: ${NOME}"
    echo "============================================"
    # Le o HOME atual do /etc/passwd (better-root muda ele no meio do fluxo)
    PWD_HOME=$(awk -F: '$1=="root"{print $6}' /etc/passwd)
    HOME="${PWD_HOME}" sh ${SCRIPT_DIR}/${SCRIPT}
    touch ${MARCA}
}

# ---------- BASE (ordem de dependencia, nao alterar) ----------
run_step entware            features/entware/install.sh
run_step better-root-safe   installer/extras/better-root-safe/install.sh
run_step better-init        features/better-init/install.sh
run_step moonraker          features/moonraker/install.sh
run_step fluidd             features/fluidd/install.sh

# ---------- QOL sem Cartographer ----------
run_step screws_tilt_adjust features/screws_tilt_adjust/install.sh

mkdir -p /tmp/macros
run_step macros/bed_mesh    features/macros/bed_mesh/install.sh
run_step macros/m191        features/macros/m191/install.sh
run_step macros/start_print features/macros/start_print/install.sh
run_step macros/overrides   features/macros/overrides/install.sh

# ---------- OPCIONAIS (descomente para instalar) ----------
# Botao "Force Stop Homing" no Fluidd (aplica patch no webhooks.py do Klipper):
#run_step abort_homing       features/abort_homing/install.sh

# Pula o self-test da Creality no boot e ajusta screensaver:
#run_step skip-setup         features/skip-setup/install.sh

# Purga adaptativa KAMP (LINE_PURGE) - ATENCAO: exige mudar o
# gcode inicial no slicer (Label Objects ON + trocar purga fixa
# por LINE_PURGE). Leia features/kamp-adaptive-purge/README.md antes.
#run_step kamp               features/kamp-adaptive-purge/install.sh

echo ""
echo "============================================"
echo " Instalacao concluida!"
echo " Fluidd: http://$(ip route get 1 2>/dev/null | awk '{print $7; exit}'):4408"
echo " (se a porta 4408 nao responder, tente a 80)"
echo ""
echo " PROXIMO PASSO: atualizar o gcode inicial no slicer:"
echo " START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] CHAMBER_TEMP=[overall_chamber_temperature] MATERIAL={filament_type[initial_tool]}"
echo "============================================"
