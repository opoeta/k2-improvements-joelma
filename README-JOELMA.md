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

entware, better-root-safe, better-init, moonraker atualizado, **Fluidd** (com câmera WebRTC), `SCREWS_TILT_CALCULATE` (nivelamento dos 4 parafusos com prtouch) e as macros: `START_PRINT` paramétrico com offset por material, `MESH_IF_NEEDED` (perfis de mesh por temperatura mesa+câmara, ex. `60c_0c`), `M191` (câmara com assistência da mesa) e `overrides.cfg`.

## Opcionais (comentados no `no-carto-joelma.sh`)

`abort_homing` (botão Force Stop Homing no Fluidd), `skip-setup` (pula self-test no boot), `kamp-adaptive-purge` (LINE_PURGE adaptativo — exige mudar o gcode do slicer; funciona sem Cartographer).

## Excluído

`cartographer` e dependentes (`prtouch-cleanup`, `surface-selection-wrapper`, `cartographer-offset-setup`, `cartographer-macros`, flash do probe), `axis_twist_compensation` (o autor desaconselha), `motor-state-guard` (UNTESTED), `obico` (WIP), `secure-auth` (risco de lockout).

## Depois de instalar — slicer

Trocar o gcode inicial da máquina por:

```
START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] CHAMBER_TEMP=[overall_chamber_temperature] MATERIAL={filament_type[initial_tool]}
```

## Avisos

- Incompatível com a auto-calibração da Creality (`forced_leveling: false` no overrides).
- O `START_PRINT` aplica Z-offset por material via `SET_GCODE_OFFSET` — migrar os valores do sistema `APLICA_ZOFFSET` existente para as variáveis `_START_PRINT_VARS` (via `overrides.cfg`) para não somar offsets duas vezes.
- Firmware mais novo que 1.1.5.2: território não testado pelo repositório — rode a verificação e confira antes de instalar.
- O primeiro print de cada combinação de temperatura cria o mesh na hora; os seguintes reutilizam o perfil salvo.
