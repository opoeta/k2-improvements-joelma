; OrcaSlicer - G-code de troca de filamento - K2 Plus + CFS + K2_FLUSH
; Mesmo corte/carga do Creality Print (M8200 P/C/R/L/O); a PURGA e decidida pela
; impressora: K2_FLUSH recebe o total que o Orca calculou (flush_length) e aplica
; o piso da Central (ex. 70 mm) nas trocas comuns; acima disso respeita o Orca.
; No Orca deixe "Purgar na torre de preparacao" DESLIGADO (a purga vai pra lixeira).
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
T[next_extruder]
; WIPE flush_length = [flush_length]
K2_FLUSH TOTAL={flush_length} OLD_F={old_filament_e_feedrate} NEW_F={new_filament_e_feedrate} T_NEW=[new_filament_temp] T_HIGH=[nozzle_temperature_range_high[next_extruder]] RET=[old_retract_length_toolchange]
G0 X160 F12000
G0 Y345
M8200 O
