#!/bin/ash
# ============================================================
# Pre-verificacao antes de instalar o k2-improvements na Joelma
# Roda NA IMPRESSORA via SSH. Nao modifica nada alem de criar
# um backup do printer_data/config em /mnt/UDISK.
# ============================================================

echo "=========================================="
echo " Pre-verificacao k2-improvements (Joelma)"
echo "=========================================="

# ---------- 1. Firmware ----------
FW=""
LOG="/mnt/UDISK/creality/userdata/log/upgrade-server.log"
if [ -r "$LOG" ]; then
    FW=$(grep -oE 'sys = [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' "$LOG" | tail -1 | awk '{print $3}')
fi
if [ -z "$FW" ]; then
    IMG=$(ls /mnt/UDISK/creality/upgrade/CR0CN240110C10_ota_img_V*.img 2>/dev/null | tail -1)
    [ -n "$IMG" ] && FW=$(echo "$IMG" | sed -nE 's/.*_V([0-9.]+)\.img$/\1/p')
fi
echo ""
echo "[1] Firmware detectado: ${FW:-DESCONHECIDO}"
case "$FW" in
    1.1.6.*)  echo "    OK - rota da Joelma (no-carto-joelma.sh, adaptado ao 1.1.6.x)" ;;
    1.1.5.2)  echo "    OK - rota principal deste fork (testada)" ;;
    1.1.3.13) echo "    OK - suportado (rota do upstream Jacob10383)" ;;
    1.1.2.*)  echo "    ATENCAO - firmware 1.1.2.x tem bugs conhecidos (homing invertido)."
              echo "    Recomendado atualizar para 1.1.3.13 ou 1.1.5.2 ANTES de instalar." ;;
    "")       echo "    Nao foi possivel detectar - verifique na tela: Configuracoes > Sobre" ;;
    *)        echo "    ATENCAO - versao mais nova que 1.1.5.2 (ultima testada pelo repo)."
              echo "    A Creality pode ter mudado paths ou o Klipper embarcado."
              echo "    NAO instale ainda - mande esta saida completa pro Claude"
              echo "    para conferir a compatibilidade primeiro." ;;
esac

# ---------- 2. Modulo [respond] do Klipper ----------
echo ""
echo "[2] Modulo respond do Klipper (as macros usam RESPOND):"
ACHOU=0
for D in /usr/share/klipper/klippy/extras /mnt/UDISK/root/klipper/klippy/extras /root/klipper/klippy/extras /usr/data/klipper/klippy/extras; do
    if [ -f "$D/respond.py" ]; then
        echo "    OK - encontrado em $D/respond.py"
        ACHOU=1
        break
    fi
done
if [ $ACHOU -eq 0 ]; then
    echo "    NAO ENCONTRADO - as macros do repositorio vao FALHAR."
    echo "    Me avise que eu preparo a variante das macros sem RESPOND."
    KLIPPY=$(find /usr /mnt/UDISK /root -maxdepth 4 -name "klippy" -type d 2>/dev/null | head -2)
    [ -n "$KLIPPY" ] && echo "    (diretorios klippy encontrados: $KLIPPY)"
fi

# ---------- 3. Espaco em disco ----------
echo ""
echo "[3] Espaco em /mnt/UDISK (precisa de ~500MB livres):"
df -h /mnt/UDISK | tail -1

# ---------- 4. Macros customizadas existentes ----------
echo ""
echo "[4] Macros customizadas no config atual (para nao perder):"
CFG_DIR=""
for D in /mnt/UDISK/printer_data/config /mnt/UDISK/root/printer_data/config /usr/data/printer_data/config; do
    [ -d "$D" ] && CFG_DIR="$D" && break
done
if [ -n "$CFG_DIR" ]; then
    echo "    Config em: $CFG_DIR"
    grep -rl "CALIBRA_ZOFFSET\|APLICA_ZOFFSET\|SALVA_ZOFFSET" "$CFG_DIR" 2>/dev/null | while read F; do
        echo "    -> Macro sua encontrada em: $F"
    done
else
    echo "    Diretorio de config nao encontrado nos caminhos padrao"
fi

# ---------- 5. Backup ----------
echo ""
echo "[5] Backup do config:"
if [ -n "$CFG_DIR" ]; then
    STAMP=$(date +%Y%m%d-%H%M%S)
    BKP="/mnt/UDISK/backup-config-${STAMP}.tar.gz"
    tar czf "$BKP" -C "$(dirname $CFG_DIR)" "$(basename $CFG_DIR)" 2>/dev/null \
        && echo "    OK - salvo em $BKP" \
        || echo "    FALHOU - faca backup manual antes de continuar!"
else
    echo "    PULADO - config nao encontrado"
fi

# ---------- 6. Pecas do k2-improvements (se ja instalado) ----------
echo ""
echo "[6] Pecas do k2-improvements ja instaladas:"
ok()  { echo "    OK    - $1"; }
falta(){ echo "    FALTA - $1"; }
[ -f /usr/share/fluidd/calibra.html ] \
    && ok "Central de Calibracao (calibra.html)" || falta "Central de Calibracao"
grep -q "sensEl" /usr/share/fluidd/calibra.html 2>/dev/null \
    && ok "calibra.html na versao atual (render in-place)" \
    || falta "calibra.html atualizado (rode: joelma update)"
[ -f /usr/share/moonraker/components/joelma_info.py ] \
    && ok "componente joelma_info" || falta "componente joelma_info"
[ -f /usr/share/moonraker/components/spoolman_admin.py ] \
    && ok "componente spoolman_admin" || falta "componente spoolman_admin"
[ -f /usr/share/moonraker/components/joelma_resonances.py ] \
    && ok "componente joelma_resonances (graficos de ressonancia)" \
    || falta "componente joelma_resonances"
grep -q '^\[joelma_resonances\]' /usr/share/moonraker/moonraker.conf 2>/dev/null \
    && ok "[joelma_resonances] no moonraker.conf" || falta "[joelma_resonances] no conf"
[ -e /mnt/UDISK/printer_data/config/custom/box_guard.cfg ] \
    && ok "box_guard (blindagem do bug key171 do BOX_INFO_REFRESH)" \
    || falta "box_guard (macro de protecao do CFS)"

echo ""
echo "=========================================="
echo " Verificacao concluida. Me mande a saida"
echo " completa antes de rodar o instalador."
echo "=========================================="
