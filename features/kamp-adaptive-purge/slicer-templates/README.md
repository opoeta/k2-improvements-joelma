# Slicer templates

Drop-in machine start gcode templates for `kamp-adaptive-purge` on the K2 Plus.

| File | Slicer | Status |
| --- | --- | --- |
| `creality-print-machine-start.gcode` | Creality Print 7.x | Verified on 7.1.1 |
| `orca-machine-start.gcode` | Orca / OrcaSlicer | Unverified — `bed_type` strings need confirming against your Orca profile |

See the parent feature [README.md](../README.md) § "Slicer change required" for full setup instructions including:

- Enabling the **Label objects** toggle in your slicer (required — without it `LINE_PURGE` falls back to bed-origin behavior)
- Why a blocking `M109` is needed before `LINE_PURGE`
- Verification with `grep EXCLUDE_OBJECT_DEFINE|LINE_PURGE` on the sliced gcode

## Using a template

1. Open your slicer's printer profile → Machine G-code → Machine start G-code
2. Replace the entire block with the contents of the appropriate template
3. Save the printer profile
4. Slice a test print and verify with the grep command from the parent README before sending to the printer

## Placas nomeadas (Z-offset por placa) — PLATE=

Para quem troca muito de build plate: adicione `PLATE=<nome>` na linha
`START_PRINT` (ex.: `... CURR_BED_TYPE="{curr_bed_type}" PLATE=texturizada_antiga`).

- Cada `PLATE` diferente vira uma **placa própria** com **Z-offset próprio**
  (`zoff_<material>_<plate>`), registrada sozinha no `joelma_vars.cfg` e listada
  na Central (dropdown de placas).
- O `CURR_BED_TYPE` continua sendo passado (classifica textured/smooth pro
  fallback legado). O `PLATE` só manda na **identidade** da placa.
- Jeito prático: crie um **perfil de impressora por placa física** no fatiador,
  cada um com seu `PLATE=`. Troca de placa = troca de perfil.
- Sem `PLATE`, tudo funciona como antes (placa vem do `CURR_BED_TYPE`).
