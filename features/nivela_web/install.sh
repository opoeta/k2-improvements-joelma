#!/bin/ash
# Instala a Central de Calibracao no Fluidd stock (porta 4408)
# A pagina antiga (nivela.html) vira um redirect para calibra.html.

set -e

SCRIPT_DIR=$(readlink -f $(dirname $0))
DESTINO=/usr/share/fluidd

if [ ! -d "$DESTINO" ]; then
    echo "E: fluidd stock nao encontrado em $DESTINO"
    exit 1
fi

cp -f ${SCRIPT_DIR}/calibra.html ${DESTINO}/calibra.html

# redirect: quem tiver o link antigo cai na pagina nova
cat > ${DESTINO}/nivela.html << 'HTML'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=calibra.html">
<title>Movido para calibra.html</title>
</head>
<body style="background:#0a0c12;color:#94a3b8;font-family:system-ui;text-align:center;padding:40px">
  A Central agora fica em <a href="calibra.html" style="color:#0ea5a5">calibra.html</a>...
</body>
</html>
HTML

IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
echo "Central de Calibracao instalada: http://${IP}:4408/calibra.html"
echo "  (nivela.html redireciona para la)"
