# save-config-restart (liga/desliga pelo PAINEL — substitui o configfile.py)

Rede de segurança do `SAVE_CONFIG`: no K2, o `SAVE_CONFIG` + restart às vezes
deixa o motor sem inicializar. Esta feature faz **um `FIRMWARE_RESTART`
protegido** com watchdog que **reverte** se o `motor_control.motor_ready` não
ficar true. Mantém o limite de 5 backups de config.

Versão vendorada do Rcpilot33 (base 558 = a do seu 1.1.7.0 + 86 da feature).

## Substitui o `configfile.py` (core de boot)
Por isso **não** entra no install padrão — fica como recurso que você liga pela
Central quando quiser. Se o arquivo novo der erro de parse, o **host do Klipper
não sobe**; mas o **Moonraker/Fluidd continuam no ar**, então o **Desativar do
painel recupera** sem precisar de SSH.

## Ligar / desligar (pela Central)
Central → seção **Recursos avançados** → **SAVE_CONFIG protegido** → **Ativar**
(ou **Desativar**). O painel faz **backup** (`configfile.py.joelma-orig`, uma
vez), troca por symlink, **reinicia o Klipper sozinho** (~30 s) e mostra
**ATIVO/inativo**. Confirme que a tela volta depois do restart.
(Backend: componente `joelma_features` → `POST /server/joelma/features`.)

## Rollback automático
O **Desativar** do painel restaura o `configfile.py` de fábrica e reinicia.
Como o Moonraker fica de pé mesmo se o host do Klipper cair, dá sempre pra
desativar pela Central.

> O `install.sh` deste diretório segue existindo para instalação manual via
> SSH, mas **o caminho recomendado é o painel**.
