# Handoff — sessão de calibração da K2 Plus (out/2026)

> Para a próxima sessão (com acesso SSH direto à impressora). Leia também `CLAUDE.md`,
> `docs/K2-HANDOFF.md` e `docs/REFERENCIAS-EXTERNAS.md`. Idioma: **pt-BR**.

## Contexto fixo
- Creality **K2 Plus**, firmware **1.1.7.0**, 2 CFS, **DXC2** (dual-drive + cortador), PR Touch (bico = sonda).
  IP `10.10.1.240`, SSH `root` (senha de fábrica da K2 ou chave; **não** gravar senha no git).
- Objetivo do usuário: "melhor que uma Bambu". Regra dele: **tudo ligável/desligável pelo painel, com o estado
  visível, simples de operar**. Deploys em **PowerShell** (`ssh root@IP "tr -d '\r' | ash"`).
- Repo no GitHub: `opoeta/k2-improvements-joelma` (URL raw ainda usa esse nome). Branch de trabalho
  `claude/reler-rfid-button-safety-dig21s`, **PR #68 (rascunho)**, head `92a5d5a`. **Nunca marcar ready nem
  fazer merge sem OK explícito.**
- Quer um **fork unificado** das descobertas de outros repos: lista em `docs/REFERENCIAS-EXTERNAS.md`.

## O que foi entregue nesta sessão (tudo em commits no branch)
Central (`features/nivela_web/calibra.html`): 4 abas; barra fixa do celular (±0.005…±0.1, "placa/material");
status/temperaturas/versões fixos no topo; rotation_distance guiado e **persistente** (`rot_dist`, reaplicado
por `_K2_ROT_APLICA`); **mapa do CFS** com nº do fatiador por slot + "Conferir arquivo × CFS" + alerta de slot
vazio; **cliente só-leitura da porta 9999** (presença do firmware, etapa da troca, erro com código).
Macros: `K2_FLUSH` (purga da troca com piso 70 mm), purga inteligente, referência final de Z após o tilt,
LINE_PURGE dentro do envelope. Templates de fatiador em `features/kamp-adaptive-purge/slicer-templates/`
(Orca conferido contra o código do OrcaSlicer `da4d766`).

### O que o usuário confirmou ter feito deploy
Até `a25d91b` (mapa do CFS). **Não confirmado:** `0d295ed` (porta 9999) — perguntar/checar
(`grep -c w9Conecta /usr/share/fluidd/calibra.html`).

## PROBLEMAS ABERTOS (por prioridade)

### 1. Erro `key586 "Move out of range"` na troca de cor + purga fora da caixa de resíduos  ← prioridade
- Sintoma: na purga das trocas a impressora purga **fora da trash box**, dá `Move out of range: 148.059 360.148 9.623`
  / `146.100 357.876 0.202`, a firmware **pausa** (`z_safe_pause`); o usuário limpa, clica continuar e segue.
  Em 20/out, 3× `key586`. Depois a impressora reiniciou.
- Fatos: `toolhead.axis_maximum.y = 352.0` (o `stepper_y` aceita 400; os movimentos até Y=378 da troca só passam
  dentro da janela `M8200 P … M8200 O`). O log mostra dezenas de checagens de limite a cada 2 ms logo após o erro =
  **segmentos de arco** (`G2 I4 J0 P1` / `G3 I-4 J0 P1` da limpeza no batedor, em `K2_FLUSH` e no template).
  Erro ocorre ~3 s depois do `M106 S255` + `G4 P5000` da purga (o Klipper só processa o próximo comando quando a fila esvazia).
- **Hipóteses já descartadas:** (a) corte duplo DXC2 (`cut_pos_x=-7.5`, `cut_pos_y=200`, clear X=42.5 — longe);
  (b) deslocamento XY de coordenadas: observador mediu `base=(0,0)` e `tool==gcode==(133,378)` no meio de uma purga.
- **Hipóteses vivas:** (A) a Central abrindo `ws://IP:9999` a cada 4 s **durante** a troca interfere na firmware do CFS
  (cliente desde 14/out; a 1ª purga boa foi antes) → **teste barato: imprimir com a Central fechada em todos os aparelhos**;
  se resolver, mudar o cliente 9999 para só consultar com o card do CFS aberto e nunca imprimindo;
  (B) perda de passos/folga física do Y (cabeçote fisicamente fora de Y=378 enquanto o Klipper acha que está);
  (C) arco com a posição inicial errada.
- Faltou: erro textual de hoje, e as linhas do observador no instante do erro (`/tmp/watch_pos.py` — recriar; grava
  `tool=/gcode=/base=` a cada 0,5 s quando Y>330). **Com SSH direto**: rodar o observador e uma troca de cor supervisionada.
- Mitigação possível (não aplicada): trocar os arcos da limpeza por vai-e-vem em linha reta no `K2_FLUSH`
  (não cura a purga fora da caixa; só tira o gatilho da pausa).

### 2. Os G-codes novos do Orca **não chegaram ao fatiamento do usuário**
O arquivo gravado mostrava o G-code de troca **sem a guarda** e o inicial **sem `M141 S0`** (perfil não salvo ou o
.3mf traz a cópia antiga). O arquivo que ele anexou depois (`…6h48m.gcode`) já tinha a guarda e saiu certo.
Sem a guarda, filamento ≠ nº 1 → o Orca roda a troca inteira logo após o `LINE_PURGE` (corta, recolhe, purga 0 mm).
Conferir sempre: `change_filament_gcode` gravado no fim do .gcode contém `previous_extruder != next_extruder`.

### 3. Teste de retração / escorrimento (bico escorre em todas as viagens)
`rotation_distance` está **certo** (100 mm → sobrou 20,0). Pendentes: torre de retração (altura onde somem os fios,
início/passo), umidade do filamento, PA (0,06 carregado), temperatura 205–210. Fluxo da superfície inferior voltar a 1.0.

### 4. Entupimentos sempre no **T2B** (CFS 2 slot B), `key836/839`
Câmara ~32 °C (não é heat creep). Trocar o carretel p/ separar filamento de caminho; checar PTFE/engate do CFS→cabeçote.

### 5. Outros
- Re-checar o Z-offset (+0.070) após o deploy do Z final pós-tilt (`f718e0f`).
- Câmara: o Orca insere `M191` sozinho (espera) — o template agora tem `M141 S0`; para PLA o ideal é desmarcar
  "Ativar controle de temperatura da câmara" no filamento. Um interruptor "câmara: não esperar < 40 °C" no painel foi oferecido, não feito.
- Próximos itens da lista de referências: Load/Unload pelo painel via `feedInOrOut` (9999; **testar supervisionado**),
  edição pelo `modifyMaterial`, Mobileraker, stream da câmera do bico, PA por câmera (PressureAdvanceCamera + OpenCV local).
- Ainda não impresso: troca de cor real **pelo Orca** (os multicolor foram pelo Creality Print).

## Lições operacionais (economizam tempo)
- BusyBox da K2: **sem `nohup`**, `ls --time-style` não existe, `pkill -f` pode matar o próprio shell. Para daemon:
  `os.fork()+os.setsid()` em Python (ver o observador).
- RAM baixa: **nunca ler log grande em Python** (foi morto: `Killed`). Use `grep -a … | tail`.
- Sem `curl`: use `python3` + `urllib` (Moonraker em `127.0.0.1:7125`).
- Reiniciar Klipper só se `print_stats.state != printing`. `SET_EXTRUDER_ROTATION_DISTANCE` é só em runtime.
- Em print de arquivo, `T<n>` é tratado pela firmware, mas as macros `T0–T7` do DXC2 rodam (`Codex CFS Tx already loaded; skipping duplicate`).
- O Orca insere `T<n>` simples após o G-code inicial se o projeto tem >1 filamento.
- Teste da Central sem impressora: `features/nivela_web/dev-mock/` (mock do Moonraker e da 9999 + Playwright).

## Como a nova sessão deve operar a impressora (regras de segurança)
1. Começar **só lendo** (estado, erros, `box`, posições). Sem mover/aquecer sem pedir.
2. **Confirmar com o usuário antes** de: Home, mover eixos, aquecer, extrudar, `FIRMWARE_RESTART`, iniciar/cancelar print,
   editar `printer.cfg`/`box.cfg`, qualquer coisa com o cabeçote perto do cortador (X≈-7.5, Y=200) ou da caixa (Y≥345).
3. **Nunca** reiniciar/escrever na impressora durante `printing` sem OK explícito.
4. Backup antes de tocar em config (`cp arquivo arquivo.bak-AAAAMMDD`). Segredos fora do git.
5. Tudo que virar rotina → vira botão/estado visível na Central (regra do usuário).
