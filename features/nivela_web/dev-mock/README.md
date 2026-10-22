# Ambiente de teste da Central (sem impressora)

Simula o Moonraker (`:7125`) e a porta 9999 do CFS para abrir o `calibra.html` num
Chromium headless (Playwright) e conferir o painel antes de ir pra impressora.

```sh
mkdir -p /tmp/sp/mock && cp features/nivela_web/calibra.html /tmp/sp/mock/
cp features/nivela_web/dev-mock/* /tmp/sp/ && cd /tmp/sp
# o mock lê gcodes de teste em ./gcodes (ex.: um .gcode com "M8200 P S2" e "; filament_type = PLA;...")
bash roda_teste2.sh /tmp/sp shot9.js troca    # modos: troca | parado | sem (sem porta 9999)
```

Precisa de `playwright` global (`NODE_PATH=$(npm root -g)`). `roda_teste2.sh` guarda os PIDs
(não usar `pkill -f` com padrão que case com o próprio shell). Os dados dos slots no mock
são os reais do CFS do usuário (T1C vazio).
