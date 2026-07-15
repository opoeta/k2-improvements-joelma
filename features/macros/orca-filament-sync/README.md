# Sync de filamentos CFS → OrcaSlicer

Sincroniza **cor e material** dos slots do CFS para o OrcaSlicer, sem escrever
no CFS e sem o protocolo 485.

## Como funciona

O OrcaSlicer tem sync nativo de **MMU** (Happy Hare): ele lê o objeto `mmu`
do Klipper via Moonraker. Este módulo (`mmu.py`) **simula** esse MMU expondo os
slots do CFS como "gates":

- lê o objeto `box` do Klipper (mesma fonte da Central de Calibração) nos
  **dois schemas** conhecidos: `box.T1..T4` com `material_type[]`/`color_value[]`
  (K2 Plus fw 1.1.6.x — o schema real da Joelma, handoff §4) e, como fallback,
  `box.same_material` (schema K1/Stevetm2), expandindo **todos** os TNN de cada
  grupo;
- indexa os gates pela **posição física**: `gate = (caixa-1)*4 + slot`
  (T1A=0 … T1D=3, T2A=4, …) e publica `num_gates = 4×caixas` com os vazios
  como `gate_status 0` — é o que o Orca e o Fluidd esperam;
- resolve o `filamentId` do slot para tipo/nome: tabela local dos códigos
  sem-RFID (a mesma `FILAMENT_ID` do `joelma_cfs_edit`) primeiro, depois o
  catálogo Creality pelos 5 dígitos finais (spools com RFID; catálogo espelhado
  do `material_database.json` via K2-RFID / fork sandman21vs);
- **sobrepõe** as edições gravadas em `material_modify_info.json` pelo
  componente `joelma_cfs_edit` (só entradas com `editStatus=1`) — então editar
  um slot na Central aparece no Orca **ao vivo**, sem reiniciar o Klipper.

Baseado em [Stevetm2/K2_Custom_Macros](https://github.com/Stevetm2/K2_Custom_Macros)
(K2OrcaFilamentSync), adaptado para a Joelma.

> **Histórico (jul/2026):** a 1ª versão lia só `same_material` e pegava só o
> primeiro TNN de cada grupo — na Joelma (que publica `box.T1`, não
> `same_material`) os gates vinham vazios e o Fluidd mostrava
> "Mmu (disabled)" com um spool fantasma. Corrigido com o dual-schema acima.

## Lado do Orca

1. Device → Printer Agent = **Moonraker** (host da K2), salvar.
2. Aba **Filament** → clicar no ícone **Filament Sync** (aparece após o passo 1).
3. Em preferências dá pra escolher sincronizar só cor ou cor + tipo.

Testado (upstream) em K2 Plus com OrcaSlicer 2.3.2-beta2.

## Dois caminhos de sync no Orca (importante)

O Orca tem **dois** mecanismos distintos de sync de CFS — escolha pelo objetivo:

| Caminho | Como o Orca lê | Enxerga |
|---|---|---|
| **`crealityprint`** (host_type) | porta **9999**, `boxsInfo` (PR #13752, melhorado no fork do Jacob10383 / build `Nightly-Nanashi` — "Creality CFS matching improvements") | só o **RFID/hardware** — **não** vê edições da Central |
| **Moonraker + `[mmu]`** (esta feature) | objeto `mmu` via **Moonraker** | o box **+ as edições feitas na Central** (overlay do `material_modify_info.json`) |

Para **editar filamento na Central e ver no Orca**, use **Moonraker** (esta feature).
O caminho `crealityprint` mostra só o RFID, mas casa cor/material com os perfis de
forma mais refinada. Dá pra usar a build do Jacob (matching melhor) **e** apontar o
Printer Agent para Moonraker (puxa do nosso `[mmu]`, com as edições).

Build recomendada p/ matching: [Jacob10383/OrcaSlicer](https://github.com/Jacob10383/OrcaSlicer)
release **Nightly-Nanashi** (nightly `NanashiBase`), ou o upstream ≥ jun/2026.

**Sinergia com o Spoolman (build 2.5.0-Jacobean):** o commit `8a26d21` ("exact
Spoolman profile match") faz o Orca casar cada slot do CFS com o **perfil do
Spoolman por nome**. Isso conversa direto com a nossa integração: ao **nomear um
slot na Central ou vincular um spool**, o `joelma_cfs_edit` grava o `name` no
JSON do firmware → o Orca (caminho `crealityprint`) lê esse nome e casa o perfil
Spoolman exato (em vez de colapsar num filament genérico). Logo: dê nomes bons
aos slots (ou vincule spools) na Central para o matching do Orca ficar preciso.

## Objeto exposto (`mmu`)

O que o **Orca** lê (`MoonrakerPrinterAgent::fetch_hh_filament_info`):
`num_gates`, `gate_status`, `gate_material` (**tipo base** PLA/PETG/…, porque o
Orca resolve preset com `filament_id_by_type`), `gate_color` (RRGGBB sem `#`),
`gate_temperature`.

Extras pro painel MMU do **Fluidd** não aparecer "(disabled)" nem quebrar o
layout: `enabled`, `print_state`, `filament`, `tool`/`gate` (gate selecionado
via `MMU_SELECT`), `ttg_map`, `gate_spool_id`, `gate_filament_name` (nome do
catálogo/edição **+ `~NN%` restante** do `remain_len`), `gate_speed_override`,
`gate_remain` (extensão não-padrão: % restante numérico por gate, lido pelo
fork OrcaSlicer-K2-Wave) — **e um segundo objeto `mmu_machine`** (registrado
pelo próprio `mmu.py` via `add_object`), com 1 unit por caixa do CFS, 4 gates
cada, `version` = firmware real da caixa e `environment_sensor` apontando pro
**`temperature_sensor cfs_1`** (também fake, registrado no `__init__` — só
`cfs_1` pra não criar sensores fantasma) com a temperatura/umidade do CFS.
Sem o `mmu_machine` o Fluidd assume 1 gate por unit (`numGates ?? 1` no
`mixins/mmu.ts`) — era o "spool fantasma" único no painel.

## Robustez (por que o sync tinha parado)

Uma versão anterior condicionava a caixa T1 a `state == connect`; quando o
firmware reportava outro estado num instante, o `num_gates` ia a **zero** e o
Orca perdia o sync. Agora **T1 SEMPRE aparece se existir** (T2..T4 encadeadas
só aparecem conectadas ou com filamento — evita as caixas fantasma). Além
disso `get_status` **nunca** levanta exceção (devolve um `mmu` vazio porém
válido) e cada registro no `__init__` (`mmu_machine`, sensor, comandos) é
isolado num `try` — nada apaga o objeto `mmu`.

## O painel do Fluidd é a ÚNICA interface do CFS

Toda informação e ação do CFS vive no painel MMU. Os botões do painel chamam
macros `MMU_*` do Happy Hare — o `mmu.py` implementa as que têm equivalente:

| Ação no painel | Comando do Fluidd | Vira no CFS |
|---|---|---|
| Carregar / trocar tool | `MMU_CHANGE_TOOL TOOL=n` / `MMU_SELECT`+`MMU_LOAD` | `BOX_LOAD_MATERIAL TNN=…` |
| Ejetar / Descarregar | `MMU_EJECT` / `MMU_UNLOAD` | `BOX_QUIT_MATERIAL` |
| **Editar gate (cor/material/nome)** | `MMU_GATE_MAP MAP="{…}"` | grava o overlay `material_modify_info.json` |

**Editar slot pelo painel:** o `MMU_GATE_MAP` parseia o dict que o Fluidd manda
(`ast.literal_eval`) e grava o overlay que o próprio `mmu.py` lê — a cor/material
aparecem no painel **e no Orca ao vivo**, sem tocar no 485. Esvaziar o gate no
painel desmarca a edição (volta pro que o RFID diz).

**Guarda de segurança:** carregar um slot **sem filamento físico** é recusado
(mandar `BOX_LOAD_MATERIAL` num slot vazio estoura `None` no blob da Creality e
derruba o Klipper — visto ao vivo jul/2026).

`MMU_PRELOAD`, `MMU_CHECK_GATE(S)`, `MMU_RECOVER`, `MMU_UNLOCK`, `MMU_STATS`,
`MMU_SPOOLMAN` e `MMU_HOME` **não têm equivalente seguro** a partir do Klipper
(RFID re-read e Spoolman dependem do Moonraker/porta 9999): respondem uma
orientação e não fazem nada. Reler RFID / sincronizar Spoolman continuam na
tela da impressora e nas integrações do Moonraker.

**A Central (`calibra.html`) não tem mais NADA de CFS** — foi todo removido; a
página é só calibração (parafusos, papel, mesh, Z-offset, PID, ressonância).

## Quantidade de caixas no painel (configurador)

T1 sempre aparece; T2..T4 só quando conectadas ou com filamento. Se ainda
assim aparecer unit fantasma (ou você quiser fixar):

- **Central** → card CFS → seletor "Painel MMU (Fluidd)": auto / 1–4 CFS;
- ou no console: `SET_MMU_BOXES BOXES=1` (0 = auto). Persiste em
  `~/printer_data/config/.joelma_mmu.json` e aplica **ao vivo** (sem restart);
- ou `num_boxes` na seção `[mmu]` (o persistido tem precedência).

## Segurança / recuperação

- `get_status` nunca levanta exceção — CFS ausente ou JSON faltando → gates
  vazios; o Klipper não cai por causa disto.
- Additive: só um módulo em `klippy/extras/mmu.py` (symlink) e a seção `[mmu]`
  via `custom/mmu.cfg`. Não sobrescreve nenhum arquivo do Klipper.
- Se após instalar o Klipper **não subir**, remova o include:
  `sed -i '/mmu.cfg/d' ~/printer_data/config/custom/main.cfg` e
  `/etc/init.d/klipper restart`.
