# k2-improvements adaptado — K2 Plus "Joelma" (sem Cartographer)

Fork de [erondiel/k2-improvements](https://github.com/erondiel/k2-improvements) com as dependências do Cartographer removidas ou desativadas. Licença GPLv3 mantida (ver LICENSE).

## Instalação (um comando, do PC)

```sh
# Verificar (firmware, respond, espaço, backup — NÃO instala nada):
curl -sSL https://raw.githubusercontent.com/opoeta/k2-improvements-joelma/main/instalar-remoto.sh | sh -s -- 10.10.1.240

# Verificar e instalar:
curl -sSL https://raw.githubusercontent.com/opoeta/k2-improvements-joelma/main/instalar-remoto.sh | sh -s -- 10.10.1.240 install
```

Alternativa direto no shell da impressora (stock não tem wget/curl, então via python3):

```sh
python3 -c "import urllib.request,ssl;ctx=ssl._create_unverified_context();open('/tmp/bj.sh','wb').write(urllib.request.urlopen('https://raw.githubusercontent.com/opoeta/k2-improvements-joelma/main/bootstrap-joelma.sh',context=ctx).read())" && sh /tmp/bj.sh
```

## O que foi modificado em relação ao original

- `features/macros/start_print/start_print.cfg`: removidas as chamadas incondicionais `CARTOGRAPHER_SCAN_MODEL`/`CARTOGRAPHER_TOUCH_MODEL` (surface-selection wrapper). O bloco `{% if printer.cartographer %}` foi mantido — sem o probe, cai no fluxo de mesh por perfil de temperatura.
- `no-carto-joelma.sh`: instalador novo. O `no-carto.sh` original não instalava `entware` nem `better-root` (pré-requisitos de moonraker/fluidd). Usa `better-root-safe` e renova o `HOME` entre etapas.
- `verifica-joelma.sh` + `bootstrap-joelma.sh` + `instalar-remoto.sh`: verificação prévia, download com fallback triplo (curl→wget→python3) e execução remota.
- Todos os arquivos normalizados para LF (CRLF quebra o ash da impressora).

## O que é instalado (base)

entware, better-root-safe, better-init, moonraker atualizado, **Fluidd** (com câmera WebRTC), `SCREWS_TILT_CALCULATE` (nivelamento dos 4 parafusos com prtouch) e as macros: `START_PRINT` paramétrico com offset por material **e por placa** (`CURR_BED_TYPE`), `MESH_IF_NEEDED` (perfis de mesh por temperatura mesa+câmara, ex. `60c_0c`), `M191` (câmara com assistência da mesa) e `overrides.cfg`. Inclui a **Central de Calibração** (web — ver abaixo).

## Central de Calibração (web)

Painel único servido pelo Fluidd (`features/nivela_web`) que reúne toda a calibração da K2 Plus numa página só, em pt-BR, falando com o Moonraker por HTTP. O bico É o probe (célula de carga), então tudo mede quente.

- **Nivelamento dos parafusos** — wizard *Nivelamento Perfeito*, fluxo linear que termina com a mesa plana: **aperta tudo → solta N voltas (2/3/4) → mede → mostra quanto girar cada knob → re-mede → repete até ✓**. Cards com **SUBIR/DESCER**, voltas + sentido e um mostrador que **gira no sentido de girar o parafuso**; botão da próxima etapa **pulsa**. Caminhos alternativos: *só nivelar* (pula aperta/solta) e *teste de fuga da porca* (pega porca girando em falso). Medição robusta multi-passe (mediana) na 1ª leitura; **re-medições em 1 toque** (rápidas) no loop de ajuste. Convenção Klipper CW-M4: **horário sobe** o canto.
- **Probe & Z-offset** — passos de **0.005 a 0.1 mm**, **Ler valor atual** (offset aplicado + z_offset salvo no probe), **teste de 1ª camada** (quadrado sólido — perímetro + preenchimento, baseado no gcode de Z-offset do Creality Print) pra julgar o squish, `Z_OFFSET_APPLY_PROBE` + `SAVE_CONFIG` e `PROBE_ACCURACY`.
- **Pressure Advance** — aplicar/chips, **teste de LINHA de PA** que replica o padrão do Creality Print (linhas com trecho lento/rápido/lento e `SET_PRESSURE_ADVANCE` por linha) **com o valor de PA impresso ao lado** (fonte 7-seg); torre `TUNING_TOWER` como alternativa.
- **Mesh da mesa**, **PID**, **Input Shaper & ressonância** (acelerômetro LIS2DW, gráficos), **Extrusora & fluxo** (`rotation_distance`), **Velocidade & aceleração**.
- **Filament Box (CFS)** — lê os slots direto do firmware (`box.T1.filament`), Load/Unload com guarda, releitura de RFID, cadeia de runout e **sincronização com o Spoolman** (SpoolmanDB) por `extra.tag=TNN`.
- **Console ao vivo** colorido por tipo de tarefa (erro, comando, gcode, calibração, CFS, ventoinha; ruído de baixo nível apagado), calibração pela folha térmica, jog, aquecimento com presets, câmera e sensores.

Calibração pré-impressão acelerada (via `probe-speed`): viagem do mesh/z_tilt em 600 mm/s e `horizontal_move_z` do `[bed_mesh]` em 3 mm (a mesa desce menos entre os pontos).

## Também instalado

`kamp-adaptive-purge` (mesh adaptativo + `LINE_PURGE` — exige "Etiquetar objetos" no slicer; funciona sem Cartographer), `moonraker-upgrade` (Fluidd upstream + componentes `joelma_cfs_edit`/`joelma_resonances`), `nivela_web` (a Central), `box_guard` (blindagem do bug key171/key60) e `probe-speed` (mesh/z_tilt mais rápidos).

## Opcionais (comentados no `no-carto-joelma.sh`)

`abort_homing` (botão Force Stop Homing no Fluidd), `skip-setup` (pula self-test no boot).

## Excluído

`cartographer` e dependentes (`prtouch-cleanup`, `surface-selection-wrapper`, `cartographer-offset-setup`, `cartographer-macros`, flash do probe), `axis_twist_compensation` (o autor desaconselha), `motor-state-guard` (UNTESTED), `obico` (WIP), `secure-auth` (risco de lockout).

## Depois de instalar — slicer

Trocar o gcode inicial da máquina por (Creality Print / OrcaSlicer):

```
START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] CHAMBER_TEMP=[overall_chamber_temperature] MATERIAL={filament_type[initial_tool]} CURR_BED_TYPE="{curr_bed_type}" ADAPTIVE=1
```

- `MATERIAL=` ativa o Z-offset por material; `CURR_BED_TYPE=` seleciona o offset da placa (textured/smooth); `ADAPTIVE=1` faz o mesh só da área da peça (KAMP).
- **Ligue "Etiquetar objetos" (Label objects)** no slicer — sem ele o KAMP não acha os objetos e cai pra mesa inteira.
- Templates prontos em `features/kamp-adaptive-purge/slicer-templates/` (Creality Print e Orca) já incluem o `LINE_PURGE` (purga adaptativa) e um flush de limpeza de bico ao carregar o filamento.

## Avisos

- Incompatível com a auto-calibração da Creality (`forced_leveling: false` no overrides).
- O `START_PRINT` aplica Z-offset por material via `SET_GCODE_OFFSET` — migrar os valores do sistema `APLICA_ZOFFSET` existente para as variáveis `_START_PRINT_VARS` (via `overrides.cfg`) para não somar offsets duas vezes.
- Firmware mais novo que 1.1.5.2: território não testado pelo repositório — rode a verificação e confira antes de instalar.
- O primeiro print de cada combinação de temperatura cria o mesh na hora; os seguintes reutilizam o perfil salvo.
