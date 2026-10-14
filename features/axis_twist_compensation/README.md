# axis_twist_compensation (liga/desliga pelo PAINEL)

Compensa drift de Z ao longo de X/Y (melhora a 1ª camada). **Substitui o
`probe.py`** do Klipper, por isso **não** entra no install padrão — fica como
recurso que você liga quando quiser, **pela Central** (sem SSH).

Versão vendorada do Rcpilot33 (probe.py 514 ≈ stock 1.1.7.0 513 + 1 linha do
hook) — mais próxima da linhagem do seu firmware que a nossa antiga (503).

## Ligar / desligar (pela Central)
Abra a Central → seção **Recursos avançados** → **Axis Twist Compensation** →
botão **Ativar** (ou **Desativar**). O painel:

- faz **backup** do `probe.py` original (`probe.py.k2-orig`, uma vez só),
- troca por symlink pro arquivo do repo e patcha o `prtouch_v3`,
- **reinicia o Klipper sozinho** (~30 s) e mostra o status **ATIVO/inativo**.

Desativar restaura o backup e reinicia. Tudo idempotente e sem terminal.
(Backend: componente `k2_features` → `POST /server/k2/features`.)

## Calibrar
Depois de ativar, rode `AXIS_TWIST_COMPENSATION_CALIBRATE` (com o bico quente,
que é o sensor). Siga as instruções no console.

## Rollback automático
O **Desativar** do painel já reverte pro `probe.py` de fábrica. Mesmo que o
host do Klipper quebre com o arquivo novo, o Moonraker continua no ar e o botão
**Desativar** recupera. Se o probe ficar estranho (Z errado, não dispara),
desative e me avise.

> O `install.sh` deste diretório continua existindo para instalação manual via
> SSH, mas **o caminho recomendado é o painel** — ele faz backup, status e
> restart sozinho.
