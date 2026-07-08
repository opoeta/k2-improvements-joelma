#!/bin/ash
# Instala a interface web de nivelamento no Fluidd stock (porta 4408)

set -e

SCRIPT_DIR=$(readlink -f $(dirname $0))
DESTINO=/usr/share/fluidd

if [ ! -d "$DESTINO" ]; then
    echo "E: fluidd stock nao encontrado em $DESTINO"
    exit 1
fi

cp -f ${SCRIPT_DIR}/nivela.html ${DESTINO}/nivela.html
IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
echo "GUI de nivelamento instalada: http://${IP}:4408/nivela.html"
