#!/bin/sh
# ============================================================
# bootstrap-joelma.sh - roda NA IMPRESSORA (K2 Plus)
# Baixa o pacote k2-improvements-joelma direto do GitHub,
# extrai em /mnt/UDISK e roda a verificacao (padrao) ou a
# instalacao (argumento "install").
#
# Uso na impressora:
#   sh bootstrap-joelma.sh              -> so verifica
#   sh bootstrap-joelma.sh install      -> verifica e instala
#
# O firmware stock do K2 Plus nao tem wget nem curl; o download
# cai no python3 (urllib), que sempre existe no firmware.
# ============================================================

set -e

REPO="${2:-opoeta/k2-improvements-joelma}"
MODO="${1:-verificar}"
VERFILE=/mnt/UDISK/.joelma-version

URL="https://github.com/${REPO}/archive/refs/heads/main.tar.gz"
DEST=/mnt/UDISK/k2-improvements-joelma
TGZ=/mnt/UDISK/k2imp-joelma.tar.gz

echo "==> Baixando ${URL}"

baixar() {
    # 1) curl (existe se Entware ja foi instalado antes)
    if command -v curl >/dev/null 2>&1; then
        curl -sSL -o "$TGZ" "$URL" && return 0
    fi
    # 2) wget real (Entware) ou busybox wget
    if command -v wget >/dev/null 2>&1; then
        wget -q -O "$TGZ" "$URL" 2>/dev/null && return 0
        wget --no-check-certificate -q -O "$TGZ" "$URL" 2>/dev/null && return 0
    fi
    # 3) python3 urllib - sempre presente no firmware stock
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$URL" "$TGZ" << 'PYEOF' && return 0
import socket, ssl, sys, urllib.request
socket.setdefaulttimeout(60)
url, dest = sys.argv[1], sys.argv[2]
try:
    urllib.request.urlretrieve(url, dest)
except Exception:
    # fallback sem verificacao de certificado (CA bundle ausente no firmware)
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=ctx) as r, open(dest, "wb") as f:
        f.write(r.read())
PYEOF
    fi
    return 1
}

if ! baixar; then
    echo "E: download falhou por todos os metodos (curl/wget/python3)."
    echo "   Verifique se a impressora tem acesso a internet."
    exit 1
fi

echo "==> Extraindo em ${DEST}"
rm -rf "$DEST" "$DEST.tmp"
mkdir -p "$DEST.tmp"
tar xzf "$TGZ" -C "$DEST.tmp"
# o tarball do GitHub extrai como <repo>-main/
mv "$DEST.tmp"/*/ "$DEST"
rm -rf "$DEST.tmp" "$TGZ"
chmod +x "$DEST"/*.sh 2>/dev/null || true

echo "==> Rodando pre-verificacao"
sh "$DEST/verifica-joelma.sh"

if [ "$MODO" = "install" ]; then
    echo ""
    echo "==> Modo install: iniciando instalacao em 5 segundos (Ctrl+C para abortar)"
    sleep 5
    sh "$DEST/no-carto-joelma.sh"
    # registra a versao instalada e instala/atualiza o comando joelma
    SHA=$(python3 -c "import json,ssl,urllib.request;ctx=ssl._create_unverified_context();print(json.load(urllib.request.urlopen('https://api.github.com/repos/${REPO}/commits/main',context=ctx,timeout=30))['sha'][:12])" 2>/dev/null || true)
    [ -n "$SHA" ] && echo "$SHA" > $VERFILE
    cp -f "$DEST/joelma" /usr/bin/joelma && chmod +x /usr/bin/joelma
    echo "==> Comando joelma instalado (versao ${SHA:-desconhecida})"
    echo "    Proximos updates: ssh root@IP joelma update"
else
    echo ""
    echo "==> Somente verificacao executada. Para instalar:"
    echo "    sh $DEST/no-carto-joelma.sh"
fi
