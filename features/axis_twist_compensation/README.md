# axis_twist_compensation (OPT-IN — substitui o probe.py)

Compensa drift de Z ao longo de X/Y (melhora a 1ª camada). **Não** entra no
install padrão porque **substitui o `probe.py`** do Klipper.

Versão vendorada do Rcpilot33 (probe.py 514 ≈ stock 1.1.7.0 513 + 1 linha do
hook) — mais próxima da linhagem do seu firmware que a nossa antiga (503).

## Instalar (manual, consciente)
```
ssh root@IP 'sh /mnt/UDISK/k2-improvements-joelma/features/axis_twist_compensation/install.sh'
```
O install faz **backup** do `probe.py` original (`probe.py.orig.<data>`), troca
por symlink e patcha o `prtouch_v3` (se houver `.py`). **Teste o probe/homing
depois.**

## Calibrar
`AXIS_TWIST_COMPENSATION_CALIBRATE` (com o bico quente, é o sensor). Segue as
instruções no console.

## Rollback (se a sondagem quebrar)
```
ssh root@IP
EXTRAS=/usr/share/klipper/klippy/extras
rm -f $EXTRAS/probe.py
cp $(ls -t $EXTRAS/probe.py.orig.* | head -1) $EXTRAS/probe.py
/etc/init.d/klipper restart
```

⚠️ `probe.py` é core. Se o probe ficar estranho (Z errado, não dispara),
reverta e me avise.
