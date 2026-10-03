#!/bin/ash
# Fix da camera no Fluidd: a camera stock (porta 8000) deixou de aparecer no
# Fluidd. Este viewer WebRTC autossuficiente (token pela porta 9999 +
# /call/webrtc_local) e servido em /usr/share/fluidd/camera.html, acessivel em
# http://IP:4408/camera.html. Portado de HurricanePrint/Creality-K2-Camera-Fix.
# Roda DEPOIS do fluidd-upstream pra nao ser sobrescrito. Some em update de firmware.
set -e
SCRIPT_DIR=$(readlink -f $(dirname ${0}))
DESTINO=/usr/share/fluidd
if [ ! -d "$DESTINO" ]; then echo "W: fluidd nao encontrado em $DESTINO - pulando camera-fix"; exit 0; fi
cp -f ${SCRIPT_DIR}/camera.html ${DESTINO}/camera.html
IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
echo "I: camera-fix instalado -> http://${IP}:4408/camera.html"
