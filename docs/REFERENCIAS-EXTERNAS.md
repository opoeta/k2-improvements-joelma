# Referências externas — lista mestra do fork unificado

Repositórios de terceiros avaliados para o K2 Plus (firmware 1.1.7.0, CFS ×2, DXC2,
PR Touch nativo, sem Cartographer). Objetivo: este fork (`opoeta/k2-improvements`)
**une as descobertas** — trazemos peça por peça, adaptada e testada, nunca um
instalador de terceiro inteiro por cima do nosso.

Legenda: ✅ já incorporado · 🟡 vale trazer (pendente) · 🔍 checar antes · ⛔ não serve

---

## Base e origem do fork

| Repo | O que é | Status |
|---|---|---|
| [jamincollins/k2-improvements](https://github.com/jamincollins/k2-improvements) | Projeto original (macros START_PRINT, bed_mesh, overrides) | ✅ base histórica |
| [Jacob10383/k2-improvements](https://github.com/Jacob10383/k2-improvements) | Fork base deste repo; Fluidd/Moonraker do Jacob, widget do CFS | ✅ base |
| [Jacob10383/k2-plus-custom-firmware](https://github.com/Jacob10383/k2-plus-custom-firmware) | Firmware alternativa (Kalico) com `prtouch.py` e `box_*.py` **abertos** | 🔍 só se um dia trocar de firmware |
| [DnG-Crafts/K2-Camera](https://github.com/DnG-Crafts/K2-Camera) | Moonraker upstream (API 1.4) + câmera no Fluidd | ✅ `features/moonraker-upgrade` |
| DnG-Crafts/K2-Leveling | Calibração "pelo papel" | ✅ base do card Nivelamento |

## Calibração, mesh e purga

| Repo | O que tem | Status / o que fazer |
|---|---|---|
| [Rcpilot33/k2-improvements](https://github.com/Rcpilot33/k2-improvements) | Fork irmão muito ativo, foco em PR Touch nativo + Cartographer | ✅ save-config-restart, axis_twist, guarda da torre (no-sparse), **referência final de Z após o tilt** (7018984), **LINE_PURGE dentro do envelope** (1934e48). 🟡 compat. do Z-offset da **tela** (`prtouch-touchscreen`, feito p/ 1.1.5.5 — conferir no 1.1.7.0). 🟡 **stream da câmera do bico** (`installer/extras/nozzle-camera`, MJPEG :8081 — desliga a IA da Creality enquanto transmite). 🟡 `memory-diagnostics` (só se houver travamento em print longo). 🟡 heat soak cancelável. ⛔ Cartographer/R3MEN (sem o hardware). |
| [grant0013/KAMP-K2](https://github.com/grant0013/KAMP-K2) | KAMP adaptado ao K2 | ⛔ **Não se aplica ao 1.1.7.0 (verificado em 13/out/2026, print real):** o `BED_MESH_CALIBRATE ADAPTIVE=1` sondou 5×5 só na área da peça (X 122–228, Y 110.5–239.5), ou seja, o wrapper **respeita** os limites; e antes do `File opened` o master-server só faz `G28_RE_CHECK` (6 toques no centro) + `BED_MESH_PROFILE LOAD="default"` — **sem** mesh da mesa inteira, então o no-op de `G29` é desnecessário. 🟡 `purge_z_hop` (opcional). Testado só no 1.1.4.1 (K2 Combo). |
| [kyleisah/Klipper-Adaptive-Meshing-Purging](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging) | KAMP original | ✅ vendorado com PATCH K2 (`features/kamp-adaptive-purge`) |
| [undingen/PressureAdvanceCamera](https://github.com/undingen/PressureAdvanceCamera) | **PA automático por visão computacional**: imprime linhas com PA variando, fotografa com câmera apontada pra mesa e escolhe a mais lisa (OpenCV) | 🟡 **ideia forte p/ "melhor que Bambu"**: usar a **câmera do bico** da K2 (XWF-1080p6, via stream do Rcpilot33) no lugar do endoscópio USB. Pontos a resolver: foco/ângulo da câmera do bico (ele pede câmera de frente pra mesa a ~10 cm), e o recorte de fundo usa o serviço **fal.ai na nuvem** (chave paga, envia imagens) — preferir substituir por OpenCV local. Só testado no Orca; projeto em desenvolvimento inicial. |
| [Tinman-FP/Creality-K2-Plus-DXC2-Beacon](https://github.com/Tinman-FP/Creality-K2-Plus-DXC2-Beacon) | Perfil DXC2 do `[box]` + Beacon | ✅ perfil DXC2 (Tn_retrude/buffer) e rotina de calibração. 🔍 Beacon (precisa do hardware; pinado no 1.1.6.1). |

## Purga multicolor

| Repo | O que tem | Status |
|---|---|---|
| [camaro4life18/Creality-K2-Series-Purge-Volume-Fix](https://github.com/camaro4life18/Creality-K2-Series-Purge-Volume-Fix) | Intercepta `FILAMENT_RACK_FLUSH` (~100 mm fixos) com `rename_existing` | ⛔ p/ CFS: esse comando só roda na carga do **suporte externo** (`LOAD_MATERIAL`); a troca do CFS vai por `M8200`. O `M1501` que ele edita **não existe** no 1.1.7.0. 🟡 a técnica serviria p/ o suporte externo. Nossa solução p/ o CFS: `K2_FLUSH` (piso de 70 mm). |
| [military-cat/Mainsail-CFS-Panel](https://github.com/military-cat/Mainsail-CFS-Panel) (CFSail, out/2026, beta, GPL-3.0) | Painel de CFS p/ **Mainsail** falando direto com a porta **9999** (protocolo do Creality Print): `get boxsInfo` (por slot: `state` 0=vazio 1=manual 2=RFID 3=alimentando 4=retraindo, `selected`=1 carregado no bico, temp/umidade por caixa), `feedState` (etapa da troca: aquecer/cortar/purgar…), `err.key` (código de erro da tela), `set modifyMaterial` (edição confirmada por releitura; temps como float porque o K2 ignora inteiro) e **`set feedInOrOut` = Load/Unload nativo** (o firmware aquece/corta/purga). | ⛔ instalar (só Mainsail; patcheia o frontend). 🟡 **portar o protocolo p/ a Central**: (1) presença/carregado por `state`/`selected` no lugar da heurística vender/remain_len; (2) etapa da troca + código de erro ao vivo no topo; (3) **Load/Unload pelo painel via `feedInOrOut`** (resolve o key60 do `BOX_LOAD_MATERIAL`; o autor não testou fisicamente — testar supervisionado); (4) edição via `modifyMaterial` em vez de escrever os JSON. Derivado de swilsonnc/K2-plus-cfs-panel; protocolo conferido com DaviBe92/k2-websocket-re. |
| [OpenAMSOrg/openams-ui](https://github.com/OpenAMSOrg/openams-ui) | UI do OpenAMS (unidades AMS da Bambu em Klipper) | ⛔ hardware diferente. 🟡 inspiração visual: umidade/temperatura/secagem por unidade no card do CFS. |

## Interface, câmera e utilidades

| Repo | O que tem | Status |
|---|---|---|
| [tofuliang/Creality-Helper-Script-K2-Series](https://github.com/tofuliang/Creality-Helper-Script-K2-Series) | Script de menu (estilo Guilouz) que instala Fluidd/Mainsail/Moonraker/KAMP/START_PRINT próprios | ⛔ **não rodar inteiro** (sobrescreve START_PRINT/KAMP/Fluidd). 🟡 itens isolados: **Mobileraker Companion** (notificação no celular), **backup do config no GitHub**, Moonraker Timelapse. |
| [tofuliang/r2rtc](https://github.com/tofuliang/r2rtc) | Gateway WebRTC leve p/ a câmera da K2 | 🔍 comparar com nosso `camera`/`camera-fix` |
| [Guilouz/Creality-Helper-Script](https://github.com/Guilouz/Creality-Helper-Script) | Original p/ K1 | referência |
| [prestonbrown/helixscreen](https://github.com/prestonbrown/helixscreen) | Interface de toque moderna p/ Klipper; diz suportar CFS; 1.0 | ⛔ **não instalar na impressora** agora: troca a tela da Creality, e a carga do CFS só é confiável pela tela de fábrica (por G-code dá key60). 🟡 dá pra rodar num **tablet separado** ligado ao Moonraker. |
| [vsevolod-volkov/K2Plus-entware](https://github.com/vsevolod-volkov/K2Plus-entware) | Guia de instalação do Entware (feed armv7sf-k2.6) | ⛔ só README, sem persistência no boot e com bug de caminho; o nosso `features/entware` já é mais completo. |
| [Stevetm2/K2_Custom_Macros](https://github.com/Stevetm2/K2_Custom_Macros) | Macros personalizados p/ K2 | 🔍 avaliado no início do projeto; reavaliar contra o START_PRINT atual |

---

## Próximos a integrar (ordem sugerida)

1. ~~Confirmar a mesh adaptativa e a mesh pré-print do master-server (KAMP-K2)~~ — verificado: nada a fazer no 1.1.7.0.
2. 🟡 **Mobileraker Companion** — notificações no celular.
3. 🟡 **Stream da câmera do bico** (Rcpilot33) — pré-requisito do PA por câmera.
4. 🟡 **PA automático pela câmera do bico** (PressureAdvanceCamera, com OpenCV local).
5. 🟡 Backup do config no GitHub.
6. 🔍 Compat. do Z-offset da tela (Rcpilot33 `prtouch-touchscreen`) no 1.1.7.0. Até lá: **ajustar Z só pela Central/barra do celular, nunca pela tela da impressora.**
