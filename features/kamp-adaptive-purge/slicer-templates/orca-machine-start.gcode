; OrcaSlicer - G-code inicial da maquina - K2 Plus + k2-improvements
; Requisitos no Orca:
;   - Processo -> Outros -> "Etiquetar objetos" (Label objects / exclude_object) LIGADO
;     (a mesh adaptativa e o LINE_PURGE dependem disso)
;   - Impressora -> Geral -> "Usar distancias E relativas" LIGADO
; START_PRINT: preaquece, Z_TILT, mesh adaptativa so da area da peca, Z-offset
; salvo por placa+material, PA salvo. Depois o T carrega o 1o slot do CFS (o
; firmware cuida da carga), _BOX_PURGE_ON_CHANGE purga e LINE_PURGE faz a linha.
; PLATE=<nome> no fim da linha do START_PRINT = Z-offset de uma placa propria.
START_PRINT EXTRUDER_TEMP=[nozzle_temperature_initial_layer] BED_TEMP=[bed_temperature_initial_layer_single] CHAMBER_TEMP=[chamber_temperature] MATERIAL={filament_type[initial_extruder]} CURR_BED_TYPE="{curr_bed_type}" ADAPTIVE=1
T[initial_extruder]
M204 S2000
M83
M109 S[nozzle_temperature_initial_layer]
_BOX_PURGE_ON_CHANGE
LINE_PURGE
