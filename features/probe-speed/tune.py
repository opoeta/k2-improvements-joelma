#!/usr/bin/env python3
# Acelera a calibracao pre-impressao SEM mexer nos pontos de leitura: sobe o
# 'speed' (viagem entre os pontos) de [bed_mesh] e [z_tilt] no printer.cfg.
# Na Joelma vinha bed_mesh=100 e z_tilt=300 numa maquina de max_velocity=800.
#
# So mexe na linha 'speed:' DENTRO dessas secoes (nunca em probe_count/pontos).
# Idempotente (nao reescreve se ja esta >= alvo), faz backup 1x, e so grava se
# a edicao foi limpa (mesma contagem de linhas/secoes). Se o firmware update
# resetar o printer.cfg, o proximo 'joelma update' re-aplica.
import os
import re
import shutil
import sys

# alvos conservadores (bem abaixo do max_velocity=800, e a viagem entre pontos
# nao sonda -> qualquer ringing assenta antes da descida do probe)
ALVOS = {"bed_mesh": 600, "z_tilt": 600}


def main() -> int:
    cfg = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/printer_data/config/printer.cfg")
    if not os.path.isfile(cfg):
        print("I: printer.cfg nao encontrado (%s) - pulando" % cfg)
        return 0

    with open(cfg, encoding="utf-8", errors="surrogateescape") as fh:
        linhas = fh.read().split("\n")

    sec = None
    ja_mexi = set()
    saida = []
    mudou = False
    sec_re = re.compile(r"^\[([a-zA-Z0-9_]+)")
    spd_re = re.compile(r"^(\s*speed\s*:\s*)([0-9.]+)(.*)$")
    for ln in linhas:
        m = sec_re.match(ln)
        if m:
            sec = m.group(1)
        if sec in ALVOS and sec not in ja_mexi:
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
                ja_mexi.add(sec)  # so a 1a linha 'speed' de cada secao
        saida.append(ln)

    if not mudou:
        print("I: bed_mesh/z_tilt speed ja estao no alvo - nada a fazer")
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
    print("I: bed_mesh/z_tilt speed -> %s (viagem entre os pontos mais rapida)"
          % ", ".join("%s=%d" % (k, v) for k, v in ALVOS.items()))
    return 10  # 10 = mudou (o install.sh reinicia o Klipper so nesse caso)


if __name__ == "__main__":
    sys.exit(main())
