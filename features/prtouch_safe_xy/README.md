# prtouch_safe_xy — Anti-arrasto do bico no probe stock

Extensão Klippy `[k2_prtouch_safe_xy]` que enrola `_HOME_Z`/`SAFE_MOVE_Z`: recua a
mesa até `clearance_z` (padrão 30 mm) antes do 1º movimento XY, pra um contato
precoce do PR Touch não virar **arrasto do bico pela mesa**. Auto-ativa só com
`prtouch_v3` presente e **sem** Cartographer. Portado de Rcpilot33 (GPLv3).
