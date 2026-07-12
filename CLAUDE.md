# Joelma — Creality K2 Plus (fork k2-improvements-joelma)

Fork de melhorias para a K2 Plus "Joelma": Klipper + Moonraker upstream, **Central de Calibração**
web completa, integração CFS ↔ Spoolman.

## Como falar comigo

- **Português do Brasil.** Aja direto, **sem pedir confirmação**.
- Entregue **arquivos completos**, prontos pra colar. **Não use `vi`** — edite com as ferramentas
  ou `cat > arquivo << 'EOF'`.
- Código Klipper/macro: **sem acentos** (o parser da Creality quebra).
- **Preserve toda a lógica e os comentários existentes** ao modificar arquivos.
- UI compacta. Nada de botões ou telas gigantes.

## Onde as coisas estão

- **Joelma** (K2 Plus): `10.10.1.240` — firmware Creality **1.1.6.1**, placa `CR0CN240110C10`
  - Fluidd **:4408** · Moonraker **:7125** · API stock Creality **:80** e WebSocket **:9999**
  - Clone do repo na impressora: `/mnt/UDISK/k2-improvements-joelma`
  - Moonraker conf: `/usr/share/moonraker/moonraker.conf`
  - Componentes do Moonraker: `/usr/share/moonraker/components/`
- **NAS Asustor**: `10.10.1.254` — Docker rodando **Spoolman 0.23.1** em `:7912`
- Credenciais SSH: `CLAUDE.local.md` (não versionado)

## ⚠️ ARMADILHA: a página é `calibra.html`, não `nivela.html`

- **Fonte:** `features/nivela_web/calibra.html` → instalado em `/usr/share/fluidd/calibra.html`
- **URL real:** `http://10.10.1.240:4408/calibra.html`
- O `nivela.html` é apenas um **redirect gerado** pelo `install.sh`. Não existe no repo.

## Deploy (sempre este fluxo)

```powershell
git add -A; git commit -m "..."; git push
python $env:USERPROFILE\_update_joelma.py    # roda `joelma update` via SSH (~2 min)
```

As features rodam como `sh ${SCRIPT_DIR}/features/<nome>/install.sh`. Dentro do `install.sh`,
use `FEAT_DIR=$(dirname "$0")` pra achar arquivos irmãos. Blocos de config no `moonraker.conf`
devem ser **idempotentes** (`grep -q` antes de acrescentar).

## Bugs conhecidos — não tropece

1. **`BOX_INFO_REFRESH` derrubava o Klipper.** Emite internamente
   `BOX_SET_PRE_LOADING ADDR= NUM= ACTION=RUN` com parâmetros **vazios**; dentro do blob
   compilado da Creality (`box_wrapper.cpython-39.so`, sem fonte público) isso vira `None`
   (`NoneType &= int`) e o Klipper cai (`key171` + `key60`). Recupera com `FIRMWARE_RESTART`.
   **→ MITIGADO (jul/2026):** feature `macros/box_guard` intercepta o comando via
   `rename_existing` (ADDR/NUM vazios = no-op logado); a Central pede confirmação no botão
   e mostra "Recuperar (FIRMWARE_RESTART)" se cair. Validar no 1º `joelma update`.
2. **O daemon do Docker no NAS cai sozinho** (já caiu 2×). Quando cai, o Spoolman some e o
   Moonraker mostra `spoolman_connected: false`. Comando pra subir em `CLAUDE.local.md`.
3. Containers `prometheus` e `PufferPanel` ficam em restart loop no NAS — fora de escopo.

## Fatos técnicos que NÃO devem ser redescobertos

- **CFS = objeto Klipper `box`** (+ `filament_rack`), lido pelo Moonraker como qualquer
  temperatura. A **porta 9999 é WebSocket, não HTTP** (curl dá 404) — é por ela que o
  **OrcaSlicer** lê o `boxsInfo` no sync do CFS (espera cor `"#0RRGGBB"`, ignora slot sem
  `type`+`vendor`). `scripts/dump_cfs_9999.py` (roda no PC) captura o payload pra diagnóstico.
- **Precedência de exibição na Central:** rótulo local > RFID > spool vinculado. O rótulo vive
  só no navegador — o Orca lê o RFID direto da impressora e nunca vê o rótulo.
- **Nome/tema do Fluidd:** banco do Moonraker —
  `GET /server/database/item?namespace=fluidd&key=uiSettings.general.instanceName` (nome) e
  `key=uiSettings.theme` (cor primária/claro-escuro). A Central usa os dois.
- **Cor** do CFS vem como `"0RRGGBB"` (prefixo `0`) → normalizar pra `#RRGGBB`.
- **Materiais:** `000001`=PLA `002001`=PETG `003001`=ABS `004001`=TPU `005001`=ASA
  `006001`=PA `007001`=PC
- **Macros CFS:** `BOX_LOAD_MATERIAL TNN=T1A`, `BOX_QUIT_MATERIAL`, `BOX_INFO_REFRESH`,
  `BOX_EXTRUDE_MATERIAL`. Não há macro pra editar material (por isso os rótulos locais em
  `localStorage`, chave `cfsrot:{SN}:{TNN}`).
- **Luz da câmara:** `output_pin LED`, **`pwm: True`** → `SET_PIN PIN=LED VALUE=0.0..1.0`.
  É **dimerizável** (testado 0/0.25/0.5/1.0, exatos).
- **Firmware da impressora:** lido via **`fw_printenv`** (U-Boot env), não de arquivo.
  É o que o componente `joelma_info.py` faz.
- **Spoolman:** a Central fala pelo **proxy do Moonraker** (`POST /server/spoolman/proxy`,
  body `{"request_method":"GET","path":"/v1/spool"}`) pra evitar CORS.
  O `extra.tag` do spool guarda o **TNN** do slot (ex. `"T1A"`) — é assim que slot casa com spool.
- **Sensores:** não chute nomes. Auto-descubra via `GET /printer/objects/list` filtrando
  `extruder`, `heater_bed`, `heater_generic *`, `temperature_fan *`, `temperature_sensor *`.
- **Componentes próprios** (em `features/moonraker-upgrade/`, copiados pelo `install.sh`):
  - `spoolman_admin.py` → `/server/spoolman_admin/config` (GET/POST) e `/scan` (GET)
  - `joelma_info.py` → `/server/joelma/info` → `{firmware, board, modelo, modelo_cod}`
  - `joelma_resonances.py` → `/server/joelma/resonances` (lista os CSVs de
    TEST_RESONANCES/SHAPER_CALIBRATE em `/tmp`) e `/server/joelma/resonances/csv?nome=X`
    (colunas + dados) — a Central desenha os gráficos com isso.

## Verificação rápida

```powershell
curl http://10.10.1.240:7125/printer/info                     # estado do Klipper
curl -X POST http://10.10.1.240:7125/printer/firmware_restart # recuperar de shutdown
curl http://10.10.1.240:7125/server/joelma/info               # firmware da impressora
curl http://10.10.1.240:7125/server/spoolman/status           # Spoolman conectado?
curl http://10.10.1.240:7125/server/spoolman_admin/scan       # achar Spoolman na rede
```

## Detalhes completos

`docs/JOELMA-HANDOFF.md` — histórico dos commits, estrutura do objeto `box`, schema do Spoolman,
pesquisa do CFS no OrcaSlicer, receitas de curl. **Leia sob demanda.**

## Pendências (nada de código bloqueado — tudo está no ar)

- **Validar ao vivo no 1º `joelma update`:** (a) `box_guard` segura o RELER RFID — o console
  da Central deve logar `BOX_SET_PRE_LOADING ignorado: ADDR/NUM vazios` e o Klipper seguir
  ready; se o boot reclamar do `rename_existing`, remover `[include box_guard.cfg]` de
  `custom/main.cfg`; (b) gráficos de ressonância após um TEST_RESONANCES;
  (c) vínculo Spoolman no editor do slot.
- **Teste físico** da inversão APERTAR/SOLTAR: aperta um canto e remede. Se o desvio **diminuir**
  → convenção certa. Se **aumentar** → inverter 1 linha em
  `features/screws_tilt_adjust/screws_tilt_adjust.py` (`_acao_pt`) **e** o
  `const aperta = d.sign === "CCW"` no `calibra.html`.
- **Testar** o botão "Sincronizar com Spoolman" (vai criar 2 filaments novos — é esperado, veja o
  HANDOFF §5).
