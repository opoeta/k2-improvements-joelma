#!/bin/ash
# ============================================================
# cartographer_preflight.sh - diagnostico READ-ONLY (nao muda NADA)
#
# Levanta tudo que a instalacao do Cartographer precisa saber para rodar
# com seguranca no firmware 1.1.6.x da Joelma, ANTES de instalar entware
# (que faz rm -rf /opt) ou aplicar patches no Klipper (rebaseados p/ 1.1.5.2).
#
# Uso na impressora:
#   ssh root@10.10.1.240 "sh /mnt/UDISK/k2-improvements-joelma/scripts/cartographer_preflight.sh"
# ou, apos joelma update, o arquivo estara no clone do repo.
#
# Mande a saida completa pro Claude — com ela eu monto os passos exatos.
# ============================================================

echo "=================================================="
echo " Cartographer preflight (Joelma) - SO LEITURA"
echo "=================================================="

sec(){ echo ""; echo "--- $1 ---"; }
tem(){ command -v "$1" >/dev/null 2>&1 && echo "  OK   $1 -> $(command -v $1)" || echo "  FALTA $1"; }

sec "[1] Firmware / placa"
if command -v fw_printenv >/dev/null 2>&1; then
    echo "  version: $(fw_printenv version 2>/dev/null | cut -d= -f2)"
    echo "  board:   $(fw_printenv board 2>/dev/null | cut -d= -f2)"
else
    echo "  fw_printenv ausente"
fi
echo "  uname:   $(uname -a)"

sec "[2] HOME e layout (better-root cria /mnt/UDISK/root)"
echo "  HOME=$HOME"
for d in "$HOME" /mnt/UDISK/root /usr/data /root; do
    [ -d "$d" ] && echo "  existe: $d  ->  $(ls -ld $d | awk '{print $1, $3, $9}')"
done
echo "  ~/klipper:      $( [ -e $HOME/klipper ] && echo SIM || echo nao )"
echo "  ~/klippy-env:   $( [ -e $HOME/klippy-env ] && echo SIM || echo nao )"
echo "  ~/printer_data: $( [ -e $HOME/printer_data ] && echo SIM || echo nao )"

sec "[3] Klipper (path real e versao)"
for K in /usr/share/klipper /mnt/UDISK/root/klipper /root/klipper $HOME/klipper; do
    if [ -d "$K" ]; then
        echo "  klipper em: $K"
        [ -f "$K/klippy/extras/bed_mesh.py" ] && echo "    bed_mesh.py: $(wc -l < $K/klippy/extras/bed_mesh.py) linhas"
        [ -d "$K/.git" ] && echo "    git: $(cd $K && git describe --tags --always 2>/dev/null)"
        [ -f "$K/.version" ] && echo "    .version: $(cat $K/.version)"
        # tem prtouch_v3 (probe stock da Creality)?
        [ -f "$K/klippy/extras/prtouch_v3.py" ] && echo "    prtouch_v3.py: PRESENTE (probe stock)"
    fi
done

sec "[4] Python / venv do Klipper"
tem python3
echo "  python3: $(python3 --version 2>&1)"
for V in $HOME/klippy-env /usr/share/klippy-env /mnt/UDISK/root/klippy-env; do
    if [ -x "$V/bin/pip" ]; then
        echo "  klippy-env: $V"
        echo "    pip: $($V/bin/pip --version 2>&1 | head -1)"
        echo "    numpy: $($V/bin/python -c 'import numpy;print(numpy.__version__)' 2>&1 | head -1)"
        echo "    typing_extensions: $($V/bin/python -c 'import typing_extensions;print(\"ok\")' 2>&1 | head -1)"
    fi
done

sec "[5] /opt (entware faz rm -rf /opt — checar se ja tem algo)"
if [ -e /opt ]; then
    echo "  /opt existe -> $(ls -ld /opt | awk '{print $1, $11}')"
    echo "  conteudo (topo):"; ls /opt 2>/dev/null | head -20 | sed 's/^/    /'
    [ -x /opt/bin/opkg ] && echo "  opkg JA instalado: $(/opt/bin/opkg --version 2>&1 | head -1)"
else
    echo "  /opt nao existe (entware pode criar sem risco)"
fi

sec "[6] Ferramentas que o Cartographer/entware precisam"
for t in git curl wget jq unzip opkg; do tem $t; done

sec "[7] USB ACM no kernel (define se precisa do usb_bridge)"
if zcat /proc/config.gz 2>/dev/null | grep -q "CONFIG_USB_ACM=y"; then
    echo "  CONFIG_USB_ACM=y  -> USB nativo, NAO precisa de usb_bridge"
elif zcat /proc/config.gz 2>/dev/null | grep -q "CONFIG_USB_ACM=m"; then
    echo "  CONFIG_USB_ACM=m  -> modulo; checar se carrega"
else
    echo "  CONFIG_USB_ACM ausente -> PRECISA do usb_bridge (feature cartographer traz)"
fi
ls /dev/ttyACM* /dev/cartographer 2>/dev/null | sed 's/^/  serial: /' || echo "  nenhum /dev/ttyACM* ou /dev/cartographer agora (normal sem sonda plugada)"

sec "[8] Espaco em disco"
df -h / /mnt/UDISK 2>/dev/null | sed 's/^/  /'

sec "[9] Config do Klipper (probe atual)"
for C in $HOME/printer_data/config /usr/data/printer_data/config /mnt/UDISK/printer_data/config; do
    if [ -d "$C" ]; then
        echo "  config em: $C"
        grep -rlE "prtouch_v3|cartographer|scanner" "$C" 2>/dev/null | sed 's/^/    menciona probe: /'
    fi
done

sec "[10] Cartographer ja presente?"
for P in $HOME/cartographer3d-plugin /mnt/UDISK/root/cartographer3d-plugin; do
    [ -d "$P" ] && echo "  clone existe: $P ($(cd $P && git rev-parse --short HEAD 2>/dev/null))"
done

echo ""
echo "=================================================="
echo " Fim. Nada foi alterado. Mande a saida completa."
echo "=================================================="
