# HANDOFF — K2 Plus "Joelma"

Referência completa. O `CLAUDE.md` da raiz tem o essencial (carregado toda sessão); este
documento tem o histórico e os detalhes, para leitura **sob demanda**.

Credenciais SSH: `CLAUDE.local.md` (não versionado).

---

## 1. Infraestrutura

| Host | IP | O que é |
|---|---|---|
| **Joelma** (K2 Plus) | `10.10.1.240` | Impressora. Firmware Creality **1.1.6.1**, placa `CR0CN240110C10` |
| **NAS Asustor** | `10.10.1.254` | Docker: Spoolman, Obico, RomM, Portainer, AdGuard, zoukei_sync |
| **PC (Windows)** | — | Repo em `C:\Users\opoet\k2-improvements-joelma` |

Na Joelma roda o Moonraker **upstream** (fork DnG-Crafts/K2-Camera), API 1.4.0 — substitui o
build cortado da Creality. Na `:4408`, **Fluidd upstream (última release de fluidd-core/fluidd)**
via feature `fluidd-upstream` — o build da Creality fica de backup em `/usr/share/fluidd_backup`
(rollback: `rm -rf /usr/share/fluidd && cp -r /usr/share/fluidd_backup /usr/share/fluidd`).
Atualização pela própria UI: **aba Machine → Update** (`[update_manager fluidd]` no
`moonraker.conf`, `type: web`, `repo: fluidd-core/fluidd`, `path: /usr/share/fluidd`).

No NAS, **Spoolman 0.23.1** em `http://10.10.1.254:7912`. Catálogo: **24 spools, 20 filamentos,
4 fabricantes** (Masterprint, Voolt3D, Genérico, Generic).

---

## 2. Histórico dos commits

| Commit | O que entrou |
|---|---|
| `a675ddc` | Gauge SVG dos parafusos + câmera WebRTC embutida |
| `b9c745d` | Protocolo base64 da câmera + feature `moonraker-upgrade` (DnG K2-Camera: spoolman, webcam iframe, API 1.4) |
| `50574c2` | `cors_domains` com origens exatas (wildcard de IP é rejeitado pelo Moonraker 1.4) |
| `42d4050` | Inversão APERTAR/SOLTAR (os knobs da K2 ficam **embaixo** dos cantos → sentido oposto ao padrão Klipper) |
| `cd77882` | Seção CFS na Central (objeto `box`, ações BOX_*, rótulos em localStorage) |
| `cc5bf76` | Interface moderna (glassmorphism) + sincronização Spoolman↔CFS via proxy do Moonraker |
| `3a42697` | CFS: retry automático de reconexão pós-reinício |
| `e698390` | Interface responsiva + ícones SVG + botões animados + componente `spoolman_admin` + **luz da câmara com dimmer PWM** |
| `1e3d830` | **Menu completo de calibrações** + renomeia `nivela.html` → `calibra.html` (com redirect) |
| `c0062e0` | Painel de todos os sensores (auto-descoberto) + barra de sistema com firmware (`joelma_info` lê `fw_printenv`) + **mesh 3D interativo** |
| `5dd6e5a` | Mostra a versão da API quando o Moonraker não carimba a versão |
| `0cf0a05`…`4081a30` (jul/2026, PRs #1–#7) | Confirmação + botão de recuperação no RELER RFID · fix da piscada dos sensores (render in-place) · `joelma update` redeploya a Central · nome **e tema** do Fluidd aplicados na página · versão do CFS na sysbar · identidade visual Fluidd + **E-STOP** + painel de movimento (jog/Home XYZ) + aquecimento com presets + envio de G-code no console + filtro EMA das temperaturas · **gráficos de ressonância via REST** (componente `joelma_resonances`) · plano z=0 no mesh 3D · precedência rótulo/RFID/spool + **vínculo Spoolman no editor do slot** · **`box_guard`** (intercepta o bug key171) · reconexão automática do CFS pós-restart · `scripts/dump_cfs_9999.py` |

**Tudo acima está mergeado na `main`.** Pendente de validação ao vivo: ver §7.1 e as Pendências.

---

## 3. O que a Central tem hoje (`calibra.html`)

`http://10.10.1.240:4408/calibra.html`

- **Barra de sistema:** firmware da impressora · Klipper · Moonraker · CFS
- **Painel de sensores** (auto-descoberto): Bico, Mesa, Aquecedor da câmara, Ventoinha da câmara,
  Câmara, MCU — com temperatura, alvo e barra de potência
- **Gráfico** de 10 min (mesa, bico, câmara)
- **Câmera** WebRTC + **luz com dimmer** (slider 0–100%)
- **CFS:** 4 slots com cor/material/umidade, carregar, descarregar, reler RFID, rótulos locais,
  **sincronizar com Spoolman**
- **Servidor Spoolman:** configurar pela UI + **scan da rede**
- **Calibrações:** nivelamento dos parafusos (gauges), Z_TILT_ADJUST, mesh (**heatmap 3D
  interativo com plano de referência z=0**), probe & Z-offset, PID (mesa + bico + câmara),
  input shaper (LIS2DW) com **gráficos de ressonância** (CSVs de `/tmp` via
  `joelma_resonances`), pressure advance, extrusora, rotation distance, velocidade,
  diagnóstico (endstops/fan/probe/sensor de filamento), CFS cut-pos, firmware restart
- **Identidade visual do Fluidd** (Roboto, cards Material) com **nome e tema** puxados do
  próprio Fluidd (banco do Moonraker, `uiSettings`)
- **E-STOP** na app bar (dupla confirmação) + **Movimento** (jog XY/Z, Home XY/Z/XYZ, passo
  0.1–50 mm, desligar motores, posição ao vivo) + **Aquecimento** (alvos + presets)
- **Console ao vivo** com **envio de G-code** (Enter envia) e carimbo da data da cópia servida
- Sensores com **filtro EMA** (sem tremer) · slots CFS com **vínculo Spoolman** no editor

---

## 4. Estrutura do objeto `box` (CFS)

```json
box.state = "connect"
box.auto_refill = 1
box.T1 = {
  "state": "connect", "sn": "<hash RFID>", "version": "1.4.2",
  "temperature": "22", "dry_and_humidity": "51",
  "material_type": ["003001","000001","000001","-1"],
  "color_value":   ["0ffffff","0ff1e1e","07a92ac","-1"],
  "remain_len":    [...], "vender": [...]
}
box.T2/T3/T4 = "None"                              // CFS em cadeia; aqui só existe o T1
filament_rack.remain_material_color = "07a92ac"    // slot ativo
```

**Slots atuais:** T1A = ABS branco · T1B = PLA vermelho · T1C = PLA cinza-azulado (ativo) · T1D = vazio.
`TNN` aceita `T1A`..`T4D`.

---

## 5. Spoolman — schema e integração

- **spool** → aponta pra **filament** (que tem `material`, `color_hex` **sem `#`**, `vendor`).
- `extra.tag` guarda o TNN do slot como **string JSON** (ex. `"\"T1A\""`).
- As tags que já existiam no catálogo são **hashes de RFID**, não TNN — o regex
  `/^T[1-4][A-D]$/` corretamente as ignora.
- Endpoints: `GET/POST/PATCH /v1/spool`, `/v1/filament`, `/v1/vendor`, `GET /v1/info`.
- A Central fala pelo **proxy do Moonraker** (evita CORS):
  ```
  POST http://10.10.1.240:7125/server/spoolman/proxy
  body: {"request_method":"GET","path":"/v1/spool"}
  ```

⚠️ Na 1ª sincronização, o botão **"Sincronizar com Spoolman"** vai **criar filaments novos** pro
PLA vermelho e o PLA cinza — nenhum filament do catálogo bate com essas cores exatas. Isso é
**proposital**: a regra exige **material + cor exatos**, senão casava PLA vermelho com
"Dourado Silk".

---

## 6. Componentes próprios do Moonraker

Ambos em `features/moonraker-upgrade/`, copiados pelo `install.sh` para
`/usr/share/moonraker/components/` e ativados por seção no `moonraker.conf`.

**`spoolman_admin.py`**
- `GET  /server/spoolman_admin/config` → `{server, sync_rate, configurado}`
- `POST /server/spoolman_admin/config` → grava `[spoolman] server:` e **reinicia o Moonraker**
- `GET  /server/spoolman_admin/scan` → varre a subnet (portas 7912/8000/8080/7913).
  Acha `10.10.1.254:7912 v0.23.1` em ~8 s.

**`joelma_info.py`**
- `GET /server/joelma/info` → `{firmware, board, modelo, modelo_cod}`
- Lê o firmware via **`fw_printenv`** (U-Boot env) — não existe arquivo de versão útil.
- Resposta real: `{"firmware":"1.1.6.1","board":"CR0CN240110C10","modelo":"K2 Plus","modelo_cod":"F008"}`
- Códigos de modelo: `F008`=K2 Plus · `F012`=K2 Pro · `F021`=K2 · `F022`=SPARKX i7 · `F018`=Hi

**Config viva no `moonraker.conf`** (também idempotente no `install.sh`):

```ini
[spoolman]
server: http://10.10.1.254:7912
sync_rate: 5

[spoolman_admin]

[joelma_info]
```

---

## 7. Bugs conhecidos

### 7.1 ⚠️ `BOX_INFO_REFRESH` derruba o Klipper (bug do firmware da Creality)

O botão **"RELER RFID DOS SLOTS"** dispara `BOX_INFO_REFRESH`, que internamente emite
`BOX_SET_PRE_LOADING ADDR= NUM= ACTION=RUN` com os parâmetros **vazios**:

```
key171: Unable to parse 'BOX_SET_PRE_LOADING ADDR= NUM= ACTION=RUN'
key60:  Internal error on command:BOX_INFO_REFRESH
key60:  Internal error on command:BOX_SET_PRE_LOADING
```

**Recuperação:** `FIRMWARE_RESTART` (ready em ~30 s).

**Causa raiz observada (log de jul/2026):** `unsupported operand type(s) for &=: 'NoneType' and 'int'`
— o `ADDR=` vazio vira `None` dentro do módulo compilado da Creality
(`box_wrapper.cpython-39.so`, sem fonte publicado no K2_Series_Klipper).

**MITIGADO (2 camadas):**
1. A Central pede **confirmação** antes do RELER RFID e mostra o botão
   **Recuperar (FIRMWARE_RESTART)** se o Klipper cair.
2. Feature **`macros/box_guard`**: overrides via `rename_existing` — com
   `ADDR`/`NUM` vazios o comando vira no-op logado; chamada legítima repassa
   `rawparams` intacto ao original. Como os comandos internos passam pelo
   interpretador de G-code (evidência: o key171 é erro de parse), o override
   intercepta antes do módulo quebrado.
   **Validado ao vivo (jul/2026):** o guard do `BOX_SET_PRE_LOADING` funcionou
   ("ignorado: ADDR/NUM vazios" no console) — e revelou que o refresh emite uma
   **sequência**: na sequência veio `BOX_GET_RFID ADDR= NUM=`, que derrubou o
   Klipper do mesmo jeito e ganhou guard idêntico. Se aparecer key171 de OUTRO
   `BOX_*` com parâmetros vazios, adicionar mais um bloco no `box_guard.cfg`.
   ⚠️ Se o Klipper reclamar de `rename_existing` no boot, remover a linha
   `[include box_guard.cfg]` de `custom/main.cfg` e reportar.
3. **`BOX_LOAD_MATERIAL` em slot SEM filamento físico → `!! None` + shutdown**
   (jul/2026). A cadeia `BOX_LOAD_MATERIAL → BOX_LOAD_MATERIAL_EXTRUDE_MATERIAL
   → BOX_EXTRUDE_MATERIAL` estoura com `None` quando o slot não tem filamento
   presente. **Não** dá pra blindar por `rename_existing` (não é erro de parse e
   o extrude é essencial à carga). **Mitigação:** a Central só habilita "Carregar"
   quando o hardware reporta presença física (`remain_len != -1`) — rótulo/spool
   vinculado deixam o slot cheio na tela mas **não** liberam o Carregar.

### 7.2 Daemon do Docker no NAS cai sozinho

Já caiu 2×. Quando cai, o Spoolman some e o Moonraker mostra `spoolman_connected: false`.
Comando pra subir: `CLAUDE.local.md`.

Nos logs aparece `setting up IP table rules failed: (iptables not found)` — quirk do ASUSTOR,
não impede os containers de rodar.

### 7.3 Sem SFTP na impressora

O dropbear da K2 não tem SFTP. Transferência de arquivo: base64 em pedaços via `exec_command`,
decode com `python3` na impressora, conferindo `sha256`.

---

## 8. Pendências

**Decisões do Israel:**
- [x] **Botão RELER RFID:** mantido com confirmação + botão de recuperação + guarda `box_guard` (bug §7.1)
- [ ] **Teste físico da inversão APERTAR/SOLTAR:** aperta um canto e remede. Se o desvio
      **diminuir** → convenção certa. Se **aumentar** → inverter 1 linha em
      `features/screws_tilt_adjust/screws_tilt_adjust.py` (`_acao_pt`) **e** o
      `const aperta = d.sign === "CCW"` no `calibra.html`.
- [ ] Nivelamento físico pelos gauges → PID mesa/bico → SAVE_CONFIG pela Central.
- [ ] Testar o botão "Sincronizar com Spoolman" (criará 2 filaments novos — esperado).
- [ ] Ligar "Label objects" no slicer + gcode `START_PRINT ... ADAPTIVE=1`, `LINE_PURGE`.

---

## 9. OrcaSlicer + CFS — status (pesquisa jul/2026)

**O suporte nativo a CFS no K2 Plus JÁ ESTÁ MERGED.**

**PR #13752** — *"Creality K-series support: LAN discovery + CFS filament sync + filament
profiles"* (grant0013) — **mergeado pelo SoftFever em 07/jun/2026**, commit `fcfadf0` na `main`:

- **Descoberta na LAN** via mDNS/DNS-SD (o "Browse..." acha a K2 sozinho)
- **Sync do CFS**: o `CrealityPrintAgent` consulta o **WebSocket da porta 9999** (`boxsInfo`),
  lê os slots carregados e popula a sidebar pelo ícone de sync
- **Mapeamento filamento→slot** no diálogo de envio, com auto-match por material + cor,
  e suporte a spool externo
- **Multicolor**: protocolo `colorMatch` + `multiColorPrint`
- **~191 perfis** de filamento K2 (CR-PLA, Hyper PLA, CR-Silk…)
- Aba Device → Fluidd/Mainsail na `:4408`
- **Testado em K2 Plus** com fw 1.1.5.5 / CFS 1.4.2 ✅
- Requer `host_type = crealityprint`

| PR / Issue | Status |
|---|---|
| **#13752** — K-series: discovery + CFS sync + perfis | ✅ **MERGED** (07/jun) |
| **#13581** — perfis do CrealityPrint v7.1.0 | 📝 Draft/parado (conteúdo entrou via #13947) |
| **#14192** — CFS mapping **via Moonraker** | 🔓 Aberto, sem review |
| **#14191** — issue correspondente | 🔓 Aberta |
| **#14089** — follow-up família K1 (K1 SE) | 🔓 Aberta (draft) |
| **#14241** — "CFS Filament Syncing" | 🔓 Aberta |

**Detalhe:** o PR **#14192** (não mergeado) implementa o CFS **por Moonraker** e usa
**exatamente a mesma abordagem da nossa Central**: acha o objeto Klipper `box` via
`/printer/objects/list`, lê os arrays `T1..T4`, normaliza a cor `0RRGGBB`.

**Na prática:** pegue um **build nightly/beta do OrcaSlicer** (≥ 07/jun/2026) e configure com
`host_type = crealityprint`. O caminho mergeado usa a porta 9999, que continua rodando na Joelma
mesmo com o Moonraker upstream. **Atenção:** a Joelma está na **1.1.6.1**, mais nova que as
1.1.5.x testadas — se der diferença de payload, é reportável no #14241.

---

## 10. Receitas de curl

```powershell
# estado do Klipper
curl http://10.10.1.240:7125/printer/info

# recuperar de shutdown
curl -X POST http://10.10.1.240:7125/printer/firmware_restart

# firmware da impressora
curl http://10.10.1.240:7125/server/joelma/info

# ler o CFS
curl -X POST http://10.10.1.240:7125/printer/objects/query `
  -H "Content-Type: application/json" `
  -d '{"objects":{"box":null,"filament_rack":null}}'

# luz (PWM 0..1)
curl -X POST http://10.10.1.240:7125/printer/gcode/script `
  -H "Content-Type: application/json" -d '{"script":"SET_PIN PIN=LED VALUE=1"}'

# Spoolman via proxy do Moonraker
curl -X POST http://10.10.1.240:7125/server/spoolman/proxy `
  -H "Content-Type: application/json" `
  -d '{"request_method":"GET","path":"/v1/spool"}'

# scan de servidores Spoolman na rede
curl http://10.10.1.240:7125/server/spoolman_admin/scan
```
