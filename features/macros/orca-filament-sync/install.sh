#!/bin/ash
# Instala o sync de filamentos CFS -> OrcaSlicer (objeto [mmu] via Moonraker).
# O modulo mmu.py vai para klippy/extras; a secao [mmu] entra via custom/.
# Additive: nao sobrescreve patches; so acrescenta um modulo e uma secao.

set -e

SCRIPT_DIR=$(readlink -f $(dirname $0))

# acha o extras do Klipper (no 1.1.6.x e /usr/share/klipper)
EXTRAS=""
for K in /usr/share/klipper /root/klipper $HOME/klipper; do
    [ -d "$K/klippy/extras" ] && EXTRAS="$K/klippy/extras" && break
done
if [ -z "$EXTRAS" ]; then
    echo "E: klippy/extras nao encontrado — abortando"
    exit 1
fi

# backup se ja existir um mmu.py diferente (nao perder nada)
if [ -e "$EXTRAS/mmu.py" ] && [ ! -L "$EXTRAS/mmu.py" ]; then
    cp -f "$EXTRAS/mmu.py" "$EXTRAS/mmu.py.orig-$(cat /proc/uptime | cut -d. -f1)" 2>/dev/null || true
    echo "I: backup do mmu.py existente"
fi
ln -sf "$SCRIPT_DIR/mmu.py" "$EXTRAS/mmu.py"
echo "I: mmu.py -> $EXTRAS/mmu.py"

# secao [mmu] via custom/main.cfg (padrao das outras macros)
test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
ln -sf ${SCRIPT_DIR}/mmu.cfg ~/printer_data/config/custom/mmu.cfg
python ${SCRIPT_DIR}/../../../scripts/ensure_included.py \
    ~/printer_data/config/custom/main.cfg mmu.cfg

/etc/init.d/klipper restart

echo "I: sync CFS->Orca instalado."
echo "   No OrcaSlicer: Printer Agent = Moonraker, salvar, e clicar no"
echo "   icone Filament Sync na aba Filament. Se o Klipper nao subir,"
echo "   remova 'custom/mmu.cfg' do include e reinicie (ver README)."
