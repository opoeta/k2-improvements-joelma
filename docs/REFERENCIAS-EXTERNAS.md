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
| [grant0013/KAMP-K2](https://github.com/grant0013/KAMP-K2) | KAMP adaptado ao K2 | 🔍 Afirma que o `prtouch_v3_wrapper` **ignora MESH_MIN/MAX** (nosso teste de jul/2026 mostrou mesh 5×5 só na área — **confirmar no 1.1.7.0** lendo `bed_mesh.mesh_min/max` durante um print). 🟡 **no-op de `G29`/`BED_MESH_CALIBRATE_START_PRINT`** p/ o master-server não fazer mesh da mesa inteira antes do arquivo abrir (`print prepared` antes de `File opened`). 🟡 `purge_z_hop`. Testado só no 1.1.4.1 (K2 Combo). |
| [kyleisah/Klipper-Adaptive-Meshing-Purging](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging) | KAMP original | ✅ vendorado com PATCH K2 (`features/kamp-adaptive-purge`) |
| [undingen/PressureAdvanceCamera](https://github.com/undingen/PressureAdvanceCamera) | **PA automático por visão computacional**: imprime linhas com PA variando, fotografa com câmera apontada pra mesa e escolhe a mais lisa (OpenCV) | 🟡 **ideia forte p/ "melhor que Bambu"**: usar a **câmera do bico** da K2 (XWF-1080p6, via stream do Rcpilot33) no lugar do endoscópio USB. Pontos a resolver: foco/ângulo da câmera do bico (ele pede câmera de frente pra mesa a ~10 cm), e o recorte de fundo usa o serviço **fal.ai na nuvem** (chave paga, envia imagens) — preferir substituir por OpenCV local. Só testado no Orca; projeto em desenvolvimento inicial. |
| [Tinman-FP/Creality-K2-Plus-DXC2-Beacon](https://github.com/Tinman-FP/Creality-K2-Plus-DXC2-Beacon) | Perfil DXC2 do `[box]` + Beacon | ✅ perfil DXC2 (Tn_retrude/buffer) e rotina de calibração. 🔍 Beacon (precisa do hardware; pinado no 1.1.6.1). |

## Purga multicolor

| Repo | O que tem | Status |
|---|---|---|
| [camaro4life18/Creality-K2-Series-Purge-Volume-Fix](https://github.com/camaro4life18/Creality-K2-Series-Purge-Volume-Fix) | Intercepta `FILAMENT_RACK_FLUSH` (~100 mm fixos) com `rename_existing` | ⛔ p/ CFS: esse comando só roda na carga do **suporte externo** (`LOAD_MATERIAL`); a troca do CFS vai por `M8200`. O `M1501` que ele edita **não existe** no 1.1.7.0. 🟡 a técnica serviria p/ o suporte externo. Nossa solução p/ o CFS: `K2_FLUSH` (piso de 70 mm). |
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

1. 🔍 **Confirmar a mesh adaptativa e a mesh pré-print do master-server** (KAMP-K2) — diagnóstico já escrito; se confirmar, no-op de `G29`/`BED_MESH_CALIBRATE_START_PRINT`.
2. 🟡 **Mobileraker Companion** — notificações no celular.
3. 🟡 **Stream da câmera do bico** (Rcpilot33) — pré-requisito do PA por câmera.
4. 🟡 **PA automático pela câmera do bico** (PressureAdvanceCamera, com OpenCV local).
5. 🟡 Backup do config no GitHub.
6. 🔍 Compat. do Z-offset da tela (Rcpilot33 `prtouch-touchscreen`) no 1.1.7.0. Até lá: **ajustar Z só pela Central/barra do celular, nunca pela tela da impressora.**
