# DXC2 — Extrusor dual-drive + corte (opt-in, gerenciado por toggle)

Macros de CFS/DXC2 portados de Tinman-FP/Creality-K2-Plus-DXC2-Beacon (**só a
parte de CFS/DXC2 — SEM o Beacon**, por decisão do projeto). Para a K2 Plus com
o kit DXC2 instalado.

## Estado: SCAFFOLD (ainda não ligado)
- `dxc2.cfg` — overrides de T0–T7 (2 CFS), BOX_CUT_MATERIAL (double-cut),
  BOX_RETRUDE_MATERIAL (retry watchdog), QUIT_MATERIAL_RETRUDE_MATERIAL e o
  DXC2_END_UNLOAD com recuperação. **Inerte** até ser incluído pelo toggle.
- **NÃO** está no `no-carto-joelma.sh` (não é instalado por padrão).

## Ativar/Desativar (a construir)
Como o `[box]` é seção única no `box.cfg`, o toggle **edita o box.cfg** (com
backup) trocando o perfil de valores:

| chave | stock (box.cfg atual) | DXC2 (ref. Tinman — ajustar ao vivo) |
|---|---|---|
| `Tn_retrude` | -10 | -18 |
| `buffer_empty_len` | 30 | 23.25 |
| `check_cut_pos_x_max` | -5.5 | -5.0 |
| `check_cut_pos_x_min` | -9.5 | -9.5 |
| `Tn_extrude_temp` | 220 | por material |

E inclui/remove este `dxc2.cfg` no `custom/main.cfg`, depois `FIRMWARE_RESTART`.

## Falta fazer
1. Plugin Moonraker `joelma_dxc2`: ler/gravar chaves do `[box]` (backup + whitelist),
   toggle de perfil, include/remove do dxc2.cfg, restart.
2. Painel DXC2 na Central (calibra.html): interruptor + calibrar corte
   (`CALIBRATE_CUT_POS`) + ajuste de valores + troca/unload.
3. Calibração real do corte (assistir a faca) + ajuste fino de `buffer_empty_len`
   / `Tn_retrude` — **só depois do hardware instalado**.
4. Rever se o slicer emite T0–T7 para 2 CFS (ajustar o mapeamento se preciso).

## Avisos
- `CALIBRATE_CUT_POS` e as edições de `box.cfg` **mexem em hardware** → painel
  sempre com `confirm()` + guarda de impressão.
- **Nunca** copiar `cut_pos_x` de outra máquina (calibrar na sua).
- `cut_pos_offset` do doc do Tinman **não existe** neste firmware (era 1.1.6.1);
  usamos as chaves reais do seu `box.cfg`.
