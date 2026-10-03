#!/bin/ash
# Disponibiliza o dxc2.cfg em custom/ (symlink) SEM incluir no main.cfg. O
# include ([include dxc2.cfg]) e gerenciado pelo toggle do painel DXC2 (plugin
# joelma_dxc2). Assim o arquivo fica pronto, mas INERTE ate o DXC2 ser ativado.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
test -d ~/printer_data/config/custom || mkdir -p ~/printer_data/config/custom
ln -sf ${SCRIPT_DIR}/dxc2.cfg ~/printer_data/config/custom/dxc2.cfg
python ${SCRIPT_DIR}/../../scripts/ensure_included.py \
    ~/printer_data/config/printer.cfg custom/main.cfg
echo "I: dxc2.cfg disponivel em custom/ (inerte; ative pelo painel DXC2 na Central)"
