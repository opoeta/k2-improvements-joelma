; ===== OrcaSlicer - troca de filamento - K2 Plus + CFS + K2_FLUSH =====
; Porte fiel do G-code de troca do Creality Print. Diferencas: sem
; multicolor_method / flush_into_skeleton / flush_length_5 (nao existem no Orca);
; os blocos FLUSH_START viram K2_FLUSH (piso da Central, ex. 70 mm, nas trocas
; comuns; acima de 90 mm respeita o Orca). "Purgar na torre" DESLIGADO.
; GUARDA (bug real, out/2026): com um filamento que NAO e o 1o da lista, o Orca roda
; este G-code logo DEPOIS do G-code inicial, tratando o T<n> do inicio como
; "filamento anterior" (previous_extruder == next_extruder). Sem a guarda a K2 corta
; e recolhe o filamento recem-carregado e a purga sai 0 mm -> a impressao comeca sem
; filamento. Com a guarda, trocar o filamento pra ele mesmo nao faz nada.
{if previous_extruder != next_extruder}
{if toolchange_count > 1}
G17
G2 Z{z_after_toolchange + 0.4} I0.86 J0.86 P1 F10000
{endif}
{if print_sequence == "by object"}
G0 Z{max_layer_z + 0.8} F900
{endif}
G1 X0 Y245 F30000
M106 S255
M8200 P S[next_extruder]
M220 S100
{if long_retractions_when_cut[previous_extruder]}
{if retraction_distances_when_cut[previous_extruder] < 30}
M8200 R E-{retraction_distances_when_cut[previous_extruder]}
{else}
M8200 R E-30
{endif}
{endif}

M400
G0 X10 Y200 F12000
SET_VELOCITY_LIMIT ACCEL=5000 ACCEL_TO_DECEL=25000
G0 F30000

M8200 C S0
SET_VELOCITY_LIMIT ACCEL=5000 ACCEL_TO_DECEL=5000
G0 Y345 F18000
G0 X139
G0 Y378
G0 X133
M8200 R
M104 S[nozzle_temperature_range_high[previous_extruder]]
M8200 L I[next_extruder]
M400
{if long_retractions_when_cut[previous_extruder]}
{if retraction_distances_when_cut[previous_extruder] < 30}
G1 E{retraction_distances_when_cut[previous_extruder]+10} F{old_filament_e_feedrate}
{else}
G1 E40 F{old_filament_e_feedrate}
{endif}
{endif}
T[next_extruder]
; WIPE flush_length = [flush_length]
; WIPE flush_length_1 = [flush_length_1]
; WIPE flush_length_2 = [flush_length_2]
; WIPE flush_length_3 = [flush_length_3]
; WIPE flush_length_4 = [flush_length_4]
K2_FLUSH TOTAL={flush_length} OLD_F={old_filament_e_feedrate} NEW_F={new_filament_e_feedrate} T_NEW=[new_filament_temp] T_HIGH=[nozzle_temperature_range_high[next_extruder]] RET=[old_retract_length_toolchange]
G0 X160 F12000
G0 Y345
M8200 O
{endif}
