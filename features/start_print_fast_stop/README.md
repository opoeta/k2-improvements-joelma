# start_print_fast_stop — START_PRINT cancelável

Extensão Klippy `[k2_start_print_fast_stop]` que torna o `START_PRINT` (e o `M191`
aninhado) **canceláveis** quando o firmware expõe a API de cancel da Creality
(≥1.1.5.5). Auto-ativa no boot só se a API existir; senão fica inerte. O install
também só liga se o `gcode.py` tiver `check_cancel`/`cancel_pending`. Portado de Rcpilot33.
