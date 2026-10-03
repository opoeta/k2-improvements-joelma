# save-config-restart (OPT-IN — substitui o configfile.py, CRÍTICO DE BOOT)

Rede de segurança do `SAVE_CONFIG`: no K2, o `SAVE_CONFIG` + restart às vezes
deixa o motor sem inicializar. Esta feature faz **um `FIRMWARE_RESTART`
protegido** com watchdog que **reverte** se o `motor_control.motor_ready` não
ficar true. Mantém o limite de 5 backups de config.

Versão vendorada do Rcpilot33 (base 558 = a do seu 1.1.7.0 + 86 da feature).

## ⚠️ NÃO entra no install padrão
Substitui o **`configfile.py`** do Klipper — se der erro de parse, o **host do
Klipper não sobe** (Moonraker/Fluidd continuam, recuperável por SSH). Por isso
é manual + com backup.

## Instalar (consciente)
```
ssh root@IP 'sh /mnt/UDISK/k2-improvements-joelma/features/save-config-restart/install.sh'
```
Faz backup (`configfile.py.orig.<data>`), troca por symlink, reinicia.
**Confirme que o Klipper sobe** (abra o Fluidd / veja `printer.info`).

## Rollback (se o Klipper não subir)
```
ssh root@IP
K=~/klipper/klippy
rm -f $K/configfile.py
cp $(ls -t $K/configfile.py.orig.* | head -1) $K/configfile.py
/etc/init.d/klipper restart
```
