#!/bin/ash
# DESINSTALADOR do sync [mmu] (emulacao Happy Hare) - jul/2026.
#
# Por que removido: o [mmu] emulava um MMU sobre o blob 'box' da Creality so
# pra (a) o OrcaSlicer sincronizar filamentos e (b) o painel MMU do Fluidd
# exibir o CFS. Os dois papeis foram substituidos:
#   (a) o Orca (fork Jacob / mainline com CFS nativo) le o CFS DIRETO pela
#       porta 9999 - sem emulacao;
#   (b) a Central de Calibracao ganhou o painel "Filament Box" (dados 100%
#       stock: objeto box + filament_switch_sensor + Spoolman + edicao ao
#       vivo pela 9999 via joelma_cfs_edit).
# Menos uma camada de traducao sobre o blob = menos superficie de shutdown.
#
# Este script e IDEMPOTENTE: remove o modulo e a secao se existirem e sai
# quieto se ja estiver limpo. A pasta continua no repo so por causa do
# run_step do no-carto-joelma.sh.

SCRIPT_DIR=$(readlink -f $(dirname $0))
MUDOU=0

# 1. remove o symlink do modulo em klippy/extras
for K in /usr/share/klipper /root/klipper $HOME/klipper; do
    if [ -L "$K/klippy/extras/mmu.py" ]; then
        rm -f "$K/klippy/extras/mmu.py"
        echo "I: removido $K/klippy/extras/mmu.py"
        MUDOU=1
    fi
done

# 2. remove a secao [mmu] do custom/
CFG=~/printer_data/config/custom/mmu.cfg
if [ -e "$CFG" ] || [ -L "$CFG" ]; then
    rm -f "$CFG"
    echo "I: removido custom/mmu.cfg"
    MUDOU=1
fi

# 3. tira o include do custom/main.cfg (sed inplace, idempotente)
MAIN=~/printer_data/config/custom/main.cfg
if [ -f "$MAIN" ] && grep -q "include mmu.cfg" "$MAIN"; then
    sed -i '/include mmu\.cfg/d' "$MAIN"
    echo "I: include mmu.cfg removido do custom/main.cfg"
    MUDOU=1
fi

# 4. so reinicia o Klipper se algo mudou de fato
if [ "$MUDOU" = "1" ]; then
    /etc/init.d/klipper restart
    echo "I: [mmu] desinstalado - CFS agora e o Filament Box da Central"
else
    echo "I: [mmu] ja estava removido - nada a fazer"
fi
