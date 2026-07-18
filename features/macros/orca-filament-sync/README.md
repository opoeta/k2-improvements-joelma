# orca-filament-sync — REMOVIDO (jul/2026)

Esta feature instalava o `[mmu]`: uma emulação de MMU (Happy Hare) sobre o
objeto `box` do CFS, para o OrcaSlicer sincronizar filamentos e o painel MMU
do Fluidd exibir o CFS. O `install.sh` desta pasta hoje é um **desinstalador
idempotente** — remove o módulo/seção da impressora no próximo `joelma update`.

## Por que foi removido

1. **O sync do Orca não precisa mais de emulação.** O OrcaSlicer com CFS
   nativo (fork Jacob / mainline — ver HANDOFF §9) lê o `boxsInfo` direto da
   **porta 9999** da impressora. É o caminho oficial do próprio CrealityPrint.
2. **A UI do CFS voltou para a Central de Calibração** como o painel
   **Filament Box** (inspirado no widget do Jacob10383, reimplementado com
   dados 100% stock): status, temperatura/umidade do CFS, caminho
   SLOT→PRINTHEAD, grade de slots com heurística anti-fantasma (`vender`),
   peso restante via Spoolman, cadeia de runout, load/unload com guarda e o
   editor de slot ao vivo (porta 9999, `joelma_cfs_edit`).
3. **Menos uma camada sobre o blob.** O `[mmu]` precisou de 3 PRs de correção
   (gate carregado, guarda anti-shutdown, cor 8-char) em uma semana. Traduzir
   o schema instável do blob para o protocolo do Happy Hare era fonte
   contínua de bugs.

## Se um dia precisar do painel MMU de volta

O código vive no histórico do git (`git log -- features/macros/orca-filament-sync/mmu.py`,
último estado em PR #35). Base original: Stevetm2/K2_Custom_Macros (GPLv3).
