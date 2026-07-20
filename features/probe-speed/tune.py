#!/usr/bin/env python3
# Acelera a calibracao pre-impressao SEM mexer nos pontos de leitura:
#  1) sobe o 'speed' (viagem entre os pontos) de [bed_mesh] e [z_tilt];
#  2) baixa o 'horizontal_move_z' de [bed_mesh] (o quanto a mesa desce entre os
#     pontos) - menos curso vertical por ponto x 25 pontos = mesh bem mais
#     rapido, estilo Bambu. Na Joelma vinha bed_mesh speed=100/hmz=5.
#
# So mexe nas linhas 'speed:' e 'horizontal_move_z:' DENTRO dessas secoes
# (nunca em probe_count/pontos). Idempotente (nao reescreve se ja esta no alvo),
# faz backup 1x, e so grava se a edicao foi limpa (mesma contagem de linhas). Se
# o firmware update resetar o printer.cfg, o proximo 'joelma update' re-aplica.
import os
import re
import shutil
import sys

# speed: SOBE ate o alvo (viagem entre pontos nao sonda -> ringing assenta antes
# da descida do probe). Bem abaixo do max_velocity=800.
ALVOS = {"bed_mesh": 600, "z_tilt": 600}
# horizontal_move_z: BAIXA ate o alvo (a mesa desce menos entre os pontos). 3mm
# ainda folga de sobra numa mesa nivelada; se ela estiver muito torta ou com
# residuo, suba de volta. So mexemos no [bed_mesh] (o z_tilt mexe na gantry, onde
# a variacao pode ser maior - fica no valor de fabrica).
HMZ_ALVOS = {"bed_mesh": 3}


def main() -> int:
    cfg = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/printer_data/config/printer.cfg")
    if not os.path.isfile(cfg):
        print("I: printer.cfg nao encontrado (%s) - pulando" % cfg)
        return 0

    with open(cfg, encoding="utf-8", errors="surrogateescape") as fh:
        linhas = fh.read().split("\n")

    sec = None
    ja_speed = set()
    ja_hmz = set()
    saida = []
    mudou = False
    sec_re = re.compile(r"^\[([a-zA-Z0-9_]+)")
    spd_re = re.compile(r"^(\s*speed\s*:\s*)([0-9.]+)(.*)$")
    hmz_re = re.compile(r"^(\s*horizontal_move_z\s*:\s*)([0-9.]+)(.*)$")
    for ln in linhas:
        m = sec_re.match(ln)
        if m:
            sec = m.group(1)
        # speed: SOBE ate o alvo (so a 1a linha 'speed' de cada secao)
        if sec in ALVOS and sec not in ja_speed:
            sm = spd_re.match(ln)
            if sm:
                alvo = ALVOS[sec]
                try:
                    atual = float(sm.group(2))
                except ValueError:
                    atual = None
                if atual is not None and atual < alvo:
                    ln = "%s%s%s" % (sm.group(1), alvo, sm.group(3))
                    mudou = True
                ja_speed.add(sec)
        # horizontal_move_z: BAIXA ate o alvo (so a 1a de cada secao)
        elif sec in HMZ_ALVOS and sec not in ja_hmz:
            hm = hmz_re.match(ln)
            if hm:
                alvo = HMZ_ALVOS[sec]
                try:
                    atual = float(hm.group(2))
                except ValueError:
                    atual = None
                if atual is not None and atual > alvo:
                    ln = "%s%s%s" % (hm.group(1), alvo, hm.group(3))
                    mudou = True
                ja_hmz.add(sec)
        saida.append(ln)

    if not mudou:
        print("I: bed_mesh/z_tilt ja estao no alvo (speed + horizontal_move_z) - nada a fazer")
        return 0

    # sanity: nao pode ter mudado a estrutura (so o valor de umas linhas)
    if len(saida) != len(linhas):
        print("E: contagem de linhas mudou - abortando por seguranca")
        return 1

    bak = cfg + ".joelma-speed-bak"
    if not os.path.exists(bak):
        shutil.copy2(cfg, bak)
        print("I: backup em %s" % bak)
    with open(cfg, "w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.write("\n".join(saida))
    print("I: bed_mesh/z_tilt speed -> 600 e bed_mesh horizontal_move_z -> 3 "
          "(viagem mais rapida + mesa desce menos entre os pontos)")
    return 10  # 10 = mudou (o install.sh reinicia o Klipper so nesse caso)


if __name__ == "__main__":
    sys.exit(main())
