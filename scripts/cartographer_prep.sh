#!/bin/ash
# ============================================================
# cartographer_prep.sh - PREPARA o sistema para o Cartographer no 1.1.6.x
#
# Faz SO a parte SEGURA e reversivel (o que o Israel pediu: "instale os
# pacotes que faltam e deixe preparado para futuro uso"):
#   1. entware (opkg) + git/curl/unzip  -> os pacotes que faltam
#   2. typing_extensions no klippy-env   -> unica dep Python faltante
#   3. clona o cartographer3d-plugin     -> em $HOME (inerte sem o shim)
#   4. posiciona o binario usb_bridge    -> so um arquivo, nao inicia nada
#
# NAO faz a parte ARRISCADA (fica para um passo separado, validado a mao):
#   - NAO aplica os patches de Klipper (bed_mesh.py/mcu.py/... sao rebaseados
#     p/ 1.1.5.2; sobrescrever o Klipper 1.1.6.1 pode quebrar o boot)
#   - NAO mexe em printer.cfg nem cria o shim cartographer.py
#   - NAO inicia servico nem toca na sonda
#
# Ambiente confirmado pelo preflight (jul/2026): HOME=/root,
# klippy-env=/usr/share/klippy-env, /opt vazio, numpy 1.20.1 presente,
# git/curl/unzip ausentes, sem CONFIG_USB_ACM (precisa do usb_bridge).
#
# Uso:  ssh root@10.10.1.240 "sh /mnt/UDISK/k2-improvements-joelma/scripts/cartographer_prep.sh"
# ============================================================

set -e

REPO=$(readlink -f "$(dirname "$0")/..")
ENV=/usr/share/klippy-env
PLUGIN_DIR="${HOME}/cartographer3d-plugin"

echo "=================================================="
echo " Cartographer PREP (Joelma 1.1.6.x) - parte segura"
echo "=================================================="

# ---------- guardas de seguranca ----------
FW=$(fw_printenv version 2>/dev/null | cut -d= -f2)
case "$FW" in
    1.1.6.*) echo "I: firmware $FW (ok)";;
    *) echo "E: firmware '$FW' != 1.1.6.x — abortando por seguranca."; exit 1;;
esac
if [ -e /opt ] && [ "$(ls -A /opt 2>/dev/null)" ]; then
    if [ -x /opt/bin/opkg ]; then
        echo "I: /opt ja tem entware — pulo a instalacao do entware"
        SKIP_ENTWARE=1
    else
        echo "E: /opt existe e NAO esta vazio nem tem opkg. Abortando pra nao apagar nada."
        echo "   Conteudo:"; ls -A /opt | sed 's/^/     /'
        exit 1
    fi
fi
if [ ! -x "${ENV}/bin/pip" ]; then
    echo "E: klippy-env nao encontrado em ${ENV}. Abortando."; exit 1
fi

# ---------- 1. entware + pacotes que faltam ----------
if [ -z "$SKIP_ENTWARE" ]; then
    echo ""; echo "==> [1/4] instalando entware + git/curl/unzip"
    sh "${REPO}/features/entware/install.sh"
fi
export PATH=/opt/bin:/opt/sbin:$PATH
for t in git curl unzip; do
    if command -v $t >/dev/null 2>&1; then echo "  OK   $t"; else
        echo "  instalando $t via opkg"; /opt/bin/opkg install $t || echo "  W: falhou $t"
    fi
done

# ---------- 2. dep Python que falta (numpy ja existe) ----------
echo ""; echo "==> [2/4] typing_extensions no klippy-env (${ENV})"
if ${ENV}/bin/python -c "import typing_extensions" 2>/dev/null; then
    echo "  ja presente"
else
    ${ENV}/bin/pip install --disable-pip-version-check --no-cache-dir typing_extensions \
        && echo "  instalado" \
        || echo "  W: pip falhou (rede? pip 9 antigo). Reporta que eu vejo alternativa."
fi
echo "  numpy: $(${ENV}/bin/python -c 'import numpy;print(numpy.__version__)' 2>&1)"

# ---------- 3. clona o plugin (inerte: sem shim, Klipper nao carrega) ----------
echo ""; echo "==> [3/4] cartographer3d-plugin em ${PLUGIN_DIR}"
if [ -d "${PLUGIN_DIR}/.git" ]; then
    echo "  ja clonado ($(cd "$PLUGIN_DIR" && git rev-parse --short HEAD 2>/dev/null))"
else
    rm -rf "${PLUGIN_DIR}"
    git clone --depth 1 https://github.com/Jacob10383/cartographer3d-plugin.git "${PLUGIN_DIR}" \
        && echo "  clonado" \
        || echo "  W: clone falhou (checa git/rede)"
fi

# ---------- 4. posiciona o usb_bridge (so o arquivo; nao inicia servico) ----------
echo ""; echo "==> [4/4] binario usb_bridge (sem iniciar servico)"
mkdir -p /mnt/UDISK/bin
ln -sf "${REPO}/features/cartographer/usb_bridge_new" /mnt/UDISK/bin/usb_bridge_new
chmod +x /mnt/UDISK/bin/usb_bridge_new 2>/dev/null || true
echo "  em /mnt/UDISK/bin/usb_bridge_new"

echo ""
echo "=================================================="
echo " PREPARADO. Nada do Klipper/printer.cfg foi tocado."
echo ""
echo " Para ATIVAR o Cartographer depois (passo ARRISCADO,"
echo " valido contra 1.1.6.1 antes) faltam:"
echo "  - shim ~/klipper/klippy/extras/cartographer.py -> ${PLUGIN_DIR}/src"
echo "  - patches de Klipper (bed_mesh/mcu/homing/...) — CONFERIR versao!"
echo "  - cartographer.cfg no printer.cfg + serial do usb_bridge"
echo "  - plugar a sonda e calibrar"
echo " Rode: joelma verificar   e mande a saida antes de ativar."
echo "=================================================="
