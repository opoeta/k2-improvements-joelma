#!/bin/bash
SP="$1"; T="$2"; MODO="$3"
cd "$SP"
python3 -I "$SP/mock_moonraker.py" > mock.log 2>&1 & P1=$!
python3 -I "$SP/mock_9999.py" "$MODO" > mock9.log 2>&1 & P3=$!
python3 -I -m http.server 8080 -d "$SP/mock" --bind 127.0.0.1 > "$SP/http.log" 2>&1 & P2=$!
sleep 1.5
NODE_PATH=$(npm root -g) node "$SP/$T" "$SP" "$MODO"
kill $P1 $P2 $P3 2>/dev/null; wait 2>/dev/null; echo "servidores encerrados"
