# Sync de filamentos CFS → OrcaSlicer

Sincroniza **cor e material** dos slots do CFS para o OrcaSlicer, sem escrever
no CFS e sem o protocolo 485.

## Como funciona

O OrcaSlicer tem sync nativo de **MMU** (Happy Hare): ele lê o objeto `mmu`
do Klipper via Moonraker. Este módulo (`mmu.py`) **simula** esse MMU expondo os
slots do CFS como "gates":

- lê o objeto `box` do Klipper (mesma fonte da Central de Calibração);
- **sobrepõe** as edições gravadas em `material_modify_info.json` pelo
  componente `joelma_cfs_edit` — então editar um slot na Central aparece no
  Orca **ao vivo**, sem reiniciar o Klipper.

Baseado em [Stevetm2/K2_Custom_Macros](https://github.com/Stevetm2/K2_Custom_Macros)
(K2OrcaFilamentSync), adaptado para a Joelma.

## Lado do Orca

1. Device → Printer Agent = **Moonraker** (host da K2), salvar.
2. Aba **Filament** → clicar no ícone **Filament Sync** (aparece após o passo 1).
3. Em preferências dá pra escolher sincronizar só cor ou cor + tipo.

Testado (upstream) em K2 Plus com OrcaSlicer 2.3.2-beta2.

## Objeto exposto (`mmu`)

`num_gates`, `gate_status`, `gate_material`, `gate_color` (RRGGBB sem `#`),
`gate_temperature` — um por slot carregado do CFS.

## Segurança / recuperação

- `get_status` nunca levanta exceção — CFS ausente ou JSON faltando → gates
  vazios; o Klipper não cai por causa disto.
- Additive: só um módulo em `klippy/extras/mmu.py` (symlink) e a seção `[mmu]`
  via `custom/mmu.cfg`. Não sobrescreve nenhum arquivo do Klipper.
- Se após instalar o Klipper **não subir**, remova o include:
  `sed -i '/mmu.cfg/d' ~/printer_data/config/custom/main.cfg` e
  `/etc/init.d/klipper restart`.
