import os
raiz = os.path.expanduser(r"~\k2-improvements-joelma")

# 1) modulo python: traducao
p = os.path.join(raiz, "features", "screws_tilt_adjust", "screws_tilt_adjust.py")
c = open(p, newline="").read()
old = "class ScrewsTiltAdjust:"
new = '''def _acao_pt(sign, full_turns, minutes):
    # Traduz o ajuste para portugues claro (exibido no dialog do Fluidd)
    fr = {5: "1/12", 6: "1/10", 10: "1/6", 15: "1/4", 20: "1/3",
          30: "1/2", 45: "3/4"}
    m = int(minutes)
    tot = full_turns * 60 + m
    if tot <= 3:
        return "OK"
    acao = "APERTAR" if sign == "CW" else "SOLTAR"
    if full_turns > 0:
        qtd = "%d volta(s)" % full_turns + (" e %dmin" % m if m > 0 else "")
    elif m in fr:
        qtd = fr[m] + " de volta"
    else:
        qtd = "%d min" % m
    return "%s %s" % (acao, qtd)


class ScrewsTiltAdjust:'''
assert old in c, "classe nao encontrada"
c = c.replace(old, new, 1)

old2 = """                self.results["screw%d" % (i + 1,)] = {'z': z, 'sign': sign,
                    'adjust': '00:00', 'is_base': True}"""
new2 = """                self.results["screw%d" % (i + 1,)] = {'z': z, 'sign': sign,
                    'adjust': 'BASE', 'adjust_raw': '00:00', 'is_base': True}"""
assert old2 in c, "bloco base nao encontrado"
c = c.replace(old2, new2)

old3 = """                self.gcode.respond_info(
                    "%s : x=%.1f, y=%.1f, z=%.5f : adjust %s %02d:%02d" %
                    (name, coord[0], coord[1], z, sign, full_turns, minutes))
                self.results["screw%d" % (i + 1,)] = {'z': z, 'sign': sign,
                    'adjust':"%02d:%02d" % (full_turns, minutes),
                    'is_base': False}"""
new3 = """                acao = _acao_pt(sign, full_turns, minutes)
                self.gcode.respond_info(
                    "%s : x=%.1f, y=%.1f, z=%.5f : %s (%s %02d:%02d)" %
                    (name, coord[0], coord[1], z, acao, sign,
                     full_turns, minutes))
                self.results["screw%d" % (i + 1,)] = {'z': z, 'sign': sign,
                    'adjust': acao,
                    'adjust_raw': "%02d:%02d" % (full_turns, minutes),
                    'is_base': False}"""
assert old3 in c, "bloco results nao encontrado"
c = c.replace(old3, new3)
open(p, "w", newline="").write(c)
print("py OK")

# 2) cfg: nomes em portugues
p2 = os.path.join(raiz, "features", "screws_tilt_adjust", "screws_tilt_adjust.cfg")
c2 = open(p2, newline="").read()
for en, pt in [("Front Left", "Dianteiro Esquerdo"), ("Front Right", "Dianteiro Direito"),
               ("Rear Right", "Traseiro Direito"), ("Rear Left", "Traseiro Esquerdo")]:
    assert en in c2, "nao achei: " + en
    c2 = c2.replace(en, pt)
open(p2, "w", newline="").write(c2)
print("cfg nomes OK")

# 3) macro: parse pelo adjust_raw
p3 = os.path.join(raiz, "features", "macros", "nivela_parafusos", "nivela_parafusos.cfg")
c3 = open(p3, newline="").read()
old5 = "{% set partes = d.adjust.split(':') %}"
new5 = "{% set partes = d.get('adjust_raw', d.adjust).split(':') %}"
assert old5 in c3, "split da macro nao encontrado"
open(p3, "w", newline="").write(c3.replace(old5, new5))
print("macro OK")

# 4) web: idem
p4 = os.path.join(raiz, "features", "nivela_web", "nivela.html")
c4 = open(p4, newline="").read()
old6 = 'const [v,m] = d.adjust.split(":").map(Number);'
new6 = 'const [v,m] = (d.adjust_raw || d.adjust).split(":").map(Number);'
assert old6 in c4, "split da web nao encontrado"
c4 = c4.replace(old6, new6)
old8 = "'<div class=\"qtd\">' + fracao(d.adjust) + \" \""
new8 = "'<div class=\"qtd\">' + fracao(d.adjust_raw || d.adjust) + \" \""
assert old8 in c4, "fracao da web nao encontrada"
c4 = c4.replace(old8, new8)
open(p4, "w", newline="").write(c4)
print("web OK")

import py_compile
py_compile.compile(p, doraise=True)
for f in (p, p2, p3, p4):
    assert b"\r" not in open(f, "rb").read(), "CRLF em " + f
print("py_compile + LF validados")
