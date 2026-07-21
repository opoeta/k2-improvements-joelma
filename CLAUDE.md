# Joelma — Creality K2 Plus (fork k2-improvements-joelma)

Fork de melhorias para a K2 Plus "Joelma": Klipper + Moonraker upstream, **Central de Calibração**
web completa, integração CFS ↔ Spoolman.

## Como falar comigo

- **Português do Brasil.** Aja direto, **sem pedir confirmação**.
- Entregue **arquivos completos**, prontos pra colar. **Não use `vi`** — edite com as ferramentas
  ou `cat > arquivo << 'EOF'`.
- Código Klipper/macro: **sem acentos** (o parser da Creality quebra). E **nunca `;` `#`
  ou `*` dentro de `MSG="..."`** de RESPOND/M117 — o parser de gcode corta comentário
  nesses chars **ignorando aspas** → "Malformed command" e a macro morre no meio.
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
4. **KAMP com `PROBE_COUNT` menor que o do config derrubava o Klipper.** O probe da K2 é
   blob compilado (`prtouch_v3_wrapper`, fw 1.1.6.1) e assume SEMPRE a grade do
   `[bed_mesh]` (5×5 = 25 pontos). O `BED_MESH_CALIBRATE` do KAMP adaptava pra 3×3 →
   `IndexError` na linha 1925 → `key60` + shutdown no meio do `START_PRINT ADAPTIVE=1`.
   **→ CORRIGIDO (jul/2026):** `Adaptive_Meshing.cfg` agora é **vendorado** em
   `features/kamp-adaptive-purge/` com o "PATCH JOELMA": área continua adaptativa,
   contagem travada na do config (5×5 parcial foi validado em produção). Nunca voltar
   o download do upstream sem reaplicar o patch.

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
- **⭐ ESCRITA no CFS ao vivo = comando `set` da porta 9999** (fonte oficial
  `CrealityOfficial/CrealityPrint`): `{"method":"set","params":{"cId":"TNN",
  "filamentsColor":"#FFRRGGBB","filamentType":"PLA","nozzleTempMin":N,"nozzleTempMax":M,
  "cPressureAdvance":P,"cBrandName":marca,"name":nome}}`. Cor em **ARGB** (`#FF`+RRGGBB),
  não o `0RRGGBB` do arquivo. Propaga pra tela/Orca **sem restart e sem 485**. Reler RFID
  de UM slot (seguro): `{"method":"set","params":{"cId":"TNN","cRFIDRefresh":1}}`.
  Já implementado em `joelma_cfs_edit.py` (`_envia_9999()` + endpoint `/cfs/rfid`).
- **Materiais:** `000001`=PLA `002001`=PETG `003001`=ABS `004001`=TPU `005001`=ASA
  `006001`=PA `007001`=PC
- **Macros CFS:** `BOX_LOAD_MATERIAL TNN=T1A`, `BOX_QUIT_MATERIAL`, `BOX_INFO_REFRESH`,
  `BOX_EXTRUDE_MATERIAL`. Não há **macro** pra editar material — a edição ao vivo é pelo
  comando `set` da porta 9999 (ver acima); os rótulos locais em `localStorage`
  (chave `cfsrot:{SN}:{TNN}`) continuam mandando na exibição da Central.
- **Luz da câmara:** `output_pin LED`, **`pwm: True`** → `SET_PIN PIN=LED VALUE=0.0..1.0`.
  É **dimerizável** (testado 0/0.25/0.5/1.0, exatos).
- **Firmware da impressora:** lido via **`fw_printenv`** (U-Boot env), não de arquivo.
  É o que o componente `joelma_info.py` faz.
- **Spoolman:** a Central fala pelo **proxy do Moonraker** (`POST /server/spoolman/proxy`,
  body `{"request_method":"GET","path":"/v1/spool"}`) pra evitar CORS.
  O `extra.tag` do spool guarda o **TNN** do slot (ex. `"T1A"`) — é assim que slot casa com spool.
- **Probe da K2 = `[prtouch_v3]`** (célula de carga do bico) e **expõe os params padrão de
  sonda**: `samples`/`samples_result`/`sample_retract_dist`/`samples_tolerance` (confirmado
  no dump). Vem `samples: 1`. O calibrador de parafusos pede **3 toques + mediana** via
  runtime no nosso `screws_tilt_adjust.py` (`SAMPLES=`/`SAMPLES_RESULT=`, escopo só da
  medição — **não** liga global, senão o G28/mesh de toda impressão fica 3× mais lento).
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
- ~~Validar o `[mmu]` corrigido~~ **[mmu] REMOVIDO (jul/2026)** — decisão do Israel:
  a emulação Happy Hare sobre o blob (3 PRs de conserto em uma semana) foi substituída
  pelo **Filament Box da Central** (dados 100% stock) + **sync nativo do Orca pela porta
  9999** (fork Jacob/mainline — não precisa mais do objeto `mmu`). O `install.sh` da
  feature `macros/orca-filament-sync` virou **desinstalador idempotente** (remove
  `klippy/extras/mmu.py`, `custom/mmu.cfg` e o include no próximo `joelma update`).
  Código antigo vive no histórico do git (até PR #35).
- **Testar o "Teste do papel"** (novo, no card Nivelamento dos parafusos): move o bico pra
  cima de cada parafuso a Z=0,10 mm usando as coordenadas do `[screws_tilt_adjust]`; limpa o
  mesh no início (`BED_MESH_CLEAR`). FRENTE ESQUERDO é a referência. **Se "não aparecer":
  é cache do navegador — Ctrl+F5** (o arquivo é copiado pelo install da nivela_web).
- **CFS = painel "Filament Box" da Central (jul/2026, substituiu o painel MMU):**
  reimplementação stock do widget do Jacob10383 no `calibra.html` — status + **temp/umidade
  do CFS** (`box.T1.temperature`/`dry_and_humidity`), bico com/sem filamento
  (`filament_switch_sensor filament_sensor`), grade de slots com **heurística
  anti-fantasma** (presença = `vender` OU `remain_len` válidos; nunca cor/material, que são
  RFID "latcheados"), peso restante via Spoolman (`extra.tag` = TNN), **cadeia de runout
  calculada no cliente** (mesmo tipo+cor; o firmware faz a troca se `auto_refill=1`),
  Load (`BOX_LOAD_MATERIAL` com confirm + guarda) / Unload (`BOX_QUIT_MATERIAL`), RFID por
  slot (`/server/joelma/cfs/rfid`) e **editor ao vivo** (`POST /server/joelma/cfs/edit` →
  porta 9999, sem restart). Encoder/buffer/clog do widget do Jacob **não existem no stock**
  (plugin fechado) — omitidos de propósito. `box.filament` é índice de seleção *stale*:
  "Loaded" só quando o sensor do printhead confirma.
- **Sync do Orca sem o `[mmu]`:** o caminho é o **CFS nativo pela porta 9999** (build do
  fork Jacob / mainline com CFS — HANDOFF §9). No Orca: impressora conectada via IP →
  sync de filamento lê o `boxsInfo` direto. O Filament Sync via "Printer Agent = Moonraker"
  (Happy Hare) **deixou de existir** junto com o `[mmu]`.
- **Testar a "Calibração pelo papel"** (base DnG-Crafts/K2-Leveling, card Nivelamento):
  "Iniciar (60°C + bico 205°C)" → aquece os dois e **espera o BICO** (M104/M109) → home com
  o bico quente (na K2 o probe é a célula de carga do bico; homear frio e medir quente dá Z
  errado) → espera a mesa (M190) → `SET_GCODE_OFFSET Z=0 MOVE=0` + `BED_MESH_CLEAR` → leva o
  bico a **Z=0,1 mm** no **Centro** (referência) e em cada canto (coords do
  `[screws_tilt_adjust]`; centro do `axis_min/max`). Folha presa=APERTA (horário),
  solta=SOLTA. "Subir 5mm" pra trocar o papel; "Encerrar" = sobe + `G28` + `TURN_OFF_HEATERS`.
  **Se "não aparecer": Ctrl+F5** (cache). Obs.: o offset fica zerado (transitório; reseta no
  restart) — re-grave seu Z-offset e crie o mesh de novo depois. Implementado na web de
  propósito (o `bl_macros.cfg` do DnG some em firmware update → erro XS3002).
- **Z-offset tem DOIS níveis (jul/2026 — causa do "offset zera quando reinicia").**
  O ajuste fino da Central usa `SET_GCODE_OFFSET` (gcode offset): **transitório** —
  zera em restart E o `START_PRINT` o **re-seta a cada print** (`offset_<material>
  + offset_placa_<placa>`, todos 0 por padrão). Persistência: (a) **por
  placa+material** (recomendado) — Central grava `zoff_<material>_<placa>` via
  `SAVE_VARIABLE` (`[save_variables]` → `joelma_vars.cfg`, instalado pelo
  start_print/install.sh com guarda anti-duplicata) e o `START_PRINT` dá
  **prioridade** a esse valor sobre a soma legada; "Limpar" grava `None` (o if
  ignora); ou (b) global — `Z_OFFSET_APPLY_PROBE` + `SAVE_CONFIG` (funde no
  probe). **Nunca os dois pra mesma correção** (aplicaria em dobro).
- **Placas são auto-registradas (jul/2026).** `<placa>` agora é o **nome real**
  da placa do slicer "slugado" (`Textured PEI Plate` → `textured_pei_plate`), não
  mais o binário. Na 1ª impressão de cada placa o `START_PRINT` grava
  `placa_<slug> = "<nome real>"` no `joelma_vars.cfg` (**grava-só-na-mudança**, pra
  poupar flash) e a Central **monta o dropdown de placas sozinha** lendo os
  `placa_*`. Cada placa física vira um offset próprio, sem hardcode. Mantém
  `PLACA_BIN` (textured/smooth) **só** pra soma legada `offset_placa_*` e como
  **fallback de compat** dos `zoff_*` binários salvos antes desta versão. O nome
  é sanitizado no Jinja (só `[a-z0-9 -]`) — evita `;`/`#`/`*` que o parser corta.
- **Pressure Advance persistente por material (jul/2026).** Mesma mecânica do
  Z-offset: a Central grava `pa_<material>` no `joelma_vars.cfg` e o `START_PRINT`
  reaplica `SET_PRESSURE_ADVANCE` a cada print (é transitório, zera no restart).
  Cadeia: material exato → material-BASE (PLA-CF cai em `pa_pla`) → `pa_default`.
  Só aplica se houver valor salvo; senão deixa o default do slicer. **Auto-PA por
  célula de carga (prtouch/CS1237, `READ_PRES` ~1280 Hz)** é experimental: a Central
  mede a contrapressão por vazão (SNR/vazão-máx); derivar o K a partir da força
  ainda é P&D (depende do sinal real da cabeça).
- **Parafusos — convenção FECHADA com fonte (pesquisa jul/2026).** Klipper
  `Config_Reference`, `screw_thread: CW-M4`: *"A clockwise rotation of the knob
  **decreases the gap** between the nozzle and the bed"* → **horário = mesa SOBE**,
  visto **de cima**, "através da mesa" (Klipper **PR #4658**: por baixo o giro aparente
  inverte — foi a causa do flip-flop dos testes físicos). Teste físico do Israel
  confirmou. Creality (manual + wiki) e DnG-Crafts **não documentam** sentido nenhum.
  - **A estrela do card é o EFEITO medido pelo probe** (`SUBIR`/`DESCER`), inequívoco:
    `sign=CW` = canto abaixo da base → **SUBIR**; `sign=CCW` = acima → **DESCER**
    (`_acao_pt` no py e `const sobe = d.sign === "CW"` no html). **Nunca inverte.**
  - A dica de sentido é **`const horario = sobe`** (CW-M4: horário diminui o gap).
    Se um teste físico contradisser de novo, é **ângulo de visão** — a resposta é o
    "se piorar, inverta" do card, **não** flipar o código.
- **Medição dos parafusos "mudava sozinha" a cada rodada (jul/2026) — causas achadas:**
  (1) o wrapper `SCREWS_TILT_CALCULATE` rodava `Z_TILT_ADJUST` antes de **cada** medição
  e os fusos motorizados re-convergiam diferente a cada rodada; (2) medição com **bico
  frio** — o probe É a célula de carga do bico e o firmware só proba a 140°C; (3) 1
  amostra por ponto (ruído da célula); (4) **bug**: o `_RELATORIO_PARAFUSOS` do console
  ainda tinha a convenção invertida (contradizia os cards). **Protocolo atual:** wrapper
  aceita `TILT=0` (mede sem re-alinhar fusos); `NIVELA_PARAFUSOS` aquece **bico 140°C**
  (`NOZ_TEMP`) + mesa e só mede quente; a Central faz **MEDIR robusto** (2 passes,
  desempate se divergir >0,03mm, mediana + repetibilidade no card) e **Re-medir (1
  passe, TILT=0)** pro loop girar-knob→conferir. Folha térmica: nivelamento manual da
  Central usa bico a **140°C** (marca a folha térmica de 0,10mm no contato, sem ooze).
- **Testar** o botão "Sincronizar com Spoolman" (vai criar 2 filaments novos — é esperado, veja o
  HANDOFF §5).
