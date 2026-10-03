# prime_tower — Scanner de footprint da 1ª camada

Extensão Klippy `[prime_tower]` que lê o G-code selecionado e calcula o retângulo
real da 1ª camada (modelo + brim + skirt + suportes + prime tower, incl. extremos
de arco) **antes** do START_PRINT mover a máquina. Serve pra:
- **mesh adaptativo** (sondar só a área da peça) e
- **KAMP** (purga fora do que vai ser impresso).

Registra `PRIME_TOWER_WAIT` (o START_PRINT espera o scan) e `KAMP_REPORT_MESH_BOUNDS`.
Fail-open: timeout/arquivo ruim → imprime normal sem a geometria. Portado de
Rcpilot33/k2-improvements (GPLv3). Pré-req no fatiador: `;LAYER_CHANGE` + Label objects.
