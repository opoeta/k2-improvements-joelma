#!/bin/sh
# ============================================================
# instalar-remoto.sh - roda NO SEU PC (Linux/Mac/WSL/Git Bash)
# Copia o bootstrap para a impressora e executa via SSH.
#
# Uso:
#   sh instalar-remoto.sh 10.10.1.240            -> so verifica
#   sh instalar-remoto.sh 10.10.1.240 install    -> verifica e instala
#
# Ou direto do GitHub, sem clonar nada:
#   curl -sSL https://raw.githubusercontent.com/opoeta/k2-improvements-joelma/main/instalar-remoto.sh | sh -s -- 10.10.1.240
# ============================================================

set -e

IP="${1:?Uso: sh instalar-remoto.sh <ip-da-impressora> [install]}"
MODO="${2:-verificar}"
REPO="opoeta/k2-improvements-joelma"
RAW="https://raw.githubusercontent.com/${REPO}/main/bootstrap-joelma.sh"
SENHA_PADRAO="creality_2024"

SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"

# Usa sshpass se existir (senha padrao da Creality); senao pede a senha
if command -v sshpass >/dev/null 2>&1; then
    SSH="sshpass -p $SENHA_PADRAO ssh $SSH_OPTS root@$IP"
    SCP="sshpass -p $SENHA_PADRAO scp $SSH_OPTS"
else
    echo "I: sshpass nao encontrado - a senha ($SENHA_PADRAO) sera pedida ate 2x"
    SSH="ssh $SSH_OPTS root@$IP"
    SCP="scp $SSH_OPTS"
fi

echo "==> Testando conexao com $IP"
$SSH "echo ok - \$(uname -a)"

# Obtem o bootstrap: local (se rodando do clone) ou baixa do GitHub
DIR=$(dirname "$0")
if [ -f "$DIR/bootstrap-joelma.sh" ]; then
    BOOT="$DIR/bootstrap-joelma.sh"
else
    BOOT=$(mktemp)
    trap 'rm -f "$BOOT"' EXIT
    echo "==> Baixando bootstrap do GitHub"
    curl -sSL -o "$BOOT" "$RAW" || wget -qO "$BOOT" "$RAW"
fi

echo "==> Enviando bootstrap para a impressora"
$SCP "$BOOT" "root@$IP:/tmp/bootstrap-joelma.sh"

echo "==> Executando na impressora (modo: $MODO)"
$SSH "sh /tmp/bootstrap-joelma.sh $MODO"

echo ""
echo "==> Concluido. Fluidd (apos instalar): http://$IP:4408"
