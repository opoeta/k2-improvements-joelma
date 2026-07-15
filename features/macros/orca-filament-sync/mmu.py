# Expoe o CFS (objeto Klipper 'box') como um MMU (Happy Hare) para:
#   - o OrcaSlicer sincronizar cor/material/% dos slots via Moonraker;
#   - o painel MMU do Fluidd mostrar TUDO (cores, material, %, temp/umidade,
#     firmware) e agir (carregar/descarregar/EDITAR slot).
#
# TODA a informacao e acao do CFS vive aqui -> aparece no painel MMU. A
# Central de Calibracao (calibra.html) nao tem mais nada de CFS.
#
# Robustez (regra de ouro): NADA aqui pode derrubar o Klipper nem apagar o
# objeto 'mmu'. get_status NUNCA levanta excecao; cada registro no __init__ e
# isolado; a caixa T1 SEMPRE aparece se existir, para o sync de cor nunca ir
# a zero silenciosamente (era a regressao da auto-deteccao por 'state').
#
# Schemas do box lidos:
#   1. K2 Plus fw 1.1.6.x (Joelma, handoff secao 4):
#        box.T1..T4 = {"state","version","temperature","dry_and_humidity",
#                      "material_type":[...],"color_value":[...],"remain_len":[...]}
#   2. Fallback K1/Stevetm2: box.same_material = [[filamentId,"0RRGGBB",
#        ["T1A",...],"PLA"], ...] (expande TODOS os TNN do grupo).
#
# get_status tambem SOBREPOE material_modify_info.json (edicoes de slot) - e
# o MESMO arquivo que o MMU_GATE_MAP (editar no painel) e o joelma_cfs_edit
# escrevem. Assim, editar um slot no painel do Fluidd propaga pro Orca AO VIVO.
#
# GPLv3 (herdado de Stevetm2/K2_Custom_Macros).
import ast
import json
import logging
import os

MODIFY = "/mnt/UDISK/creality/userdata/box/material_modify_info.json"
# override persistido do SET_MMU_BOXES (0 = auto; 1..4 = forca a quantidade)
PERSIST = os.path.expanduser("~/printer_data/config/.joelma_mmu.json")

# Codigos de 6 digitos desta impressora (slots sem RFID e editados) - mesma
# tabela FILAMENT_ID do joelma_cfs_edit.py; consultada ANTES do catalogo.
TIPO_LOCAL = {
    "000001": "PLA", "002001": "PETG", "003001": "ABS", "004001": "TPU",
    "005001": "ASA", "006001": "PA", "007001": "PC",
}
FILAMENT_ID = {v: k for k, v in TIPO_LOCAL.items()}  # tipo base -> codigo 6d

# Catalogo Creality (material_database.json; espelhado por K2-RFID e
# sandman21vs/OrcaSlicer-k1c-cfs). Spool COM RFID reporta prefixo de serie +
# estes 5 digitos finais. codigo -> (nome do produto, tipo base)
CATALOGO = {
    "00001": ("Generic PLA", "PLA"), "00002": ("Generic PLA-Silk", "PLA"),
    "00003": ("Generic PETG", "PETG"), "00004": ("Generic ABS", "ABS"),
    "00005": ("Generic TPU", "TPU"), "00006": ("Generic PLA-CF", "PLA-CF"),
    "00007": ("Generic ASA", "ASA"), "00008": ("Generic PA", "PA"),
    "00009": ("Generic PA-CF", "PA-CF"), "00010": ("Generic BVOH", "BVOH"),
    "00011": ("Generic PVA", "PVA"), "00012": ("Generic HIPS", "HIPS"),
    "00013": ("Generic PET-CF", "PET-CF"), "00014": ("Generic PETG-CF", "PETG-CF"),
    "00015": ("Generic PA6-CF", "PA-CF"), "00016": ("Generic PAHT-CF", "PA-CF"),
    "00017": ("Generic PPS", "PPS"), "00018": ("Generic PPS-CF", "PPS-CF"),
    "00019": ("Generic PP", "PP"), "00020": ("Generic PET", "PET"),
    "00021": ("Generic PC", "PC"), "00022": ("Generic PA612-CF", "PA-CF"),
    "00023": ("Generic Support PA", "PA"), "00024": ("Generic Support PLA", "PLA"),
    "00025": ("Generic PA12-CF", "PA-CF"), "00026": ("Generic TPU 64D", "TPU"),
    "00027": ("Generic PETG-GF", "PETG-GF"), "00031": ("Generic PP-CF", "PP-CF"),
    "00032": ("Generic PCTG", "PCTG"), "00033": ("Generic ASA-CF", "ASA-CF"),
    "00034": ("Generic PA6-GF", "PA-GF"), "00035": ("eSUN PLA-LW", "PLA"),
    "01001": ("Hyper PLA", "PLA"), "01002": ("Hyper L-W PLA", "PLA"),
    "01004": ("Hyper Stardust", "PLA"), "01601": ("Soleyin Ultra PLA", "PLA"),
    "02001": ("Hyper PLA-CF", "PLA-CF"), "03001": ("Hyper ABS", "ABS"),
    "04001": ("CR-PLA", "PLA"), "05001": ("CR-Silk", "PLA"),
    "06001": ("CR-PETG", "PETG"), "06002": ("Hyper PETG", "PETG"),
    "06003": ("Hyper PETG-CF", "PETG-CF"), "07001": ("CR-ABS", "ABS"),
    "07002": ("Hyper PC", "PC"), "08001": ("Ender-PLA", "PLA"),
    "09001": ("EN-PLA+", "PLA"), "09002": ("Ender Fast PLA", "PLA"),
    "10001": ("HP-TPU", "TPU"), "11001": ("CR-Nylon", "PA"),
    "12002": ("Hyper PPA-CF", "PA-CF"), "12003": ("Hyper PAHT-CF", "PA-CF"),
    "12004": ("Hyper PA612-CF", "PA-CF"), "12005": ("Hyper PA6-CF", "PA-CF"),
    "13001": ("CR-PLA Carbon", "PLA-CF"), "14001": ("CR-PLA Matte", "PLA"),
    "15001": ("CR-PLA Fluo", "PLA"), "16001": ("CR-TPU", "TPU"),
    "17001": ("CR-Wood", "PLA"), "18001": ("HP Ultra PLA", "PLA"),
    "19001": ("HP-ASA", "ASA"), "29001": ("Hyper Marble", "PLA"),
    "E1001": ("eSUN PLA+", "PLA"), "P1001": ("Panchroma PLA Satin", "PLA"),
    "P1002": ("PolySonic PLA Pro", "PLA"), "P1003": ("Panchroma PLA Matte", "PLA"),
}

TEMP_PADRAO = {
    "PLA": 220, "PETG": 240, "ABS": 260, "ASA": 260, "TPU": 230,
    "PA": 270, "PC": 270, "PVA": 220, "HIPS": 250, "PET": 260,
}
# faixa (min,max) por tipo, para gravar minTemp/maxTemp ao editar no painel
FAIXA_TEMP = {
    "PLA": (190, 240), "PETG": (220, 270), "ABS": (240, 280), "ASA": (240, 280),
    "TPU": (200, 240), "PA": (260, 300), "PC": (260, 300),
}

TIPOS_ORCA = {
    "PLA", "PLA-CF", "PETG", "PETG-CF", "PETG-GF", "PET", "PET-CF", "ABS",
    "ASA", "ASA-CF", "TPU", "PC", "PA", "PA-CF", "PA-GF", "PVA", "HIPS",
    "PP", "PP-CF", "PPS", "PPS-CF", "PCTG", "BVOH",
}


def _num(v):
    try:
        f = float(str(v).strip())
        return f if f >= 0 else None
    except (TypeError, ValueError):
        return None


def _tnn_do_gate(g):
    # 0 -> "T1A", 5 -> "T2B"
    return "T%d%s" % (g // 4 + 1, "ABCD"[g % 4])


def _norm_cor(c):
    # "0RRGGBB" / "#0RRGGBB" / "RRGGBB" -> "RRGGBB" (6 hex, upper, sem #)
    if not c:
        return ""
    c = str(c).lstrip("#")
    if len(c) == 7 and c[0] == "0":
        c = c[1:]
    return c[-6:].upper()


def _gate_do_tnn(tnn):
    t = str(tnn).strip().upper()
    if len(t) != 3 or t[0] != "T" or not t[1].isdigit():
        return None
    caixa, slot = int(t[1]), ord(t[2]) - ord("A")
    if caixa < 1 or caixa > 4 or slot < 0 or slot > 3:
        return None
    return (caixa - 1) * 4 + slot


def _tipo_base(tipo):
    t = str(tipo or "").strip().upper()
    if t in TIPOS_ORCA:
        return t
    for b in ("PETG", "PET", "PLA", "ABS", "ASA", "TPU", "PVA", "HIPS", "PC", "PA"):
        if t.startswith(b):
            return b
    return t or "PLA"


def _material_do_codigo(cod):
    cod = str(cod or "").strip()
    if cod in TIPO_LOCAL:
        t = TIPO_LOCAL[cod]
        return t, t
    ent = CATALOGO.get(cod) or (CATALOGO.get(cod[-5:]) if len(cod) >= 5 else None)
    if ent:
        return ent[0], ent[1]
    return "", "PLA"


# Segundo objeto que o painel MMU do Fluidd le (mixins/mmu.ts): sem ele o
# numGates cai no default 1 e o painel mostra 1 spool fantasma. 1 unit por
# caixa; environment_sensor -> _CfsSensor (temp/umidade no rodape da unit);
# version = firmware real da caixa.
class _MmuMachine:
    def __init__(self, dono):
        self.dono = dono

    def get_status(self, eventtime):
        try:
            _, maxbox, extras = self.dono._scan(eventtime)
            maxbox = self.dono._caixas(maxbox)
        except Exception:
            maxbox, extras = 1, {}
        st = {'num_units': max(1, maxbox)}
        for n in range(max(1, maxbox)):
            info = extras.get(n + 1, {})
            st['unit_%d' % n] = {
                'name': 'CFS %d' % (n + 1),
                'vendor': 'Creality',
                'version': info.get('versao') or '1.0',
                'num_gates': 4,
                'first_gate': n * 4,
                'selector_type': 'VirtualSelector',
                'variable_rotation_distances': False,
                'variable_bowden_lengths': False,
                'require_bowden_move': False,
                'has_bypass': False,
                'multi_gear': False,
                'environment_sensor': 'temperature_sensor cfs_%d' % (n + 1),
            }
        return st


# Sensor "fake" com temp/umidade do CFS (box.Tn). Registrado no __init__ para
# ja constar em printer.objects quando o Moonraker enumera os sensores.
class _CfsSensor:
    def __init__(self, dono, caixa):
        self.dono, self.caixa = dono, caixa

    def get_status(self, eventtime):
        try:
            _, _, extras = self.dono._scan(eventtime)
            info = extras.get(self.caixa, {})
            return {'temperature': info.get('temp') or 0.0,
                    'humidity': info.get('umid') or 0.0}
        except Exception:
            return {'temperature': 0.0, 'humidity': 0.0}


class mmu:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.id = config.getfloat("id", default=0.0)
        self.num_boxes = config.getint("num_boxes", 0, minval=0, maxval=4)
        self._le_persist()
        self.box = None
        self.gcode = None
        self.sel_gate = -1
        self._mod_cache = ({}, 0.0)
        self._scan_cache = (None, None, None, -1.0)
        self.printer.register_event_handler("klippy:connect", self._connect)

        # mmu_machine + sensores cfs_1..cfs_4 no __init__ (hora certa para o
        # Moonraker enumerar). Cada registro isolado: uma falha nao derruba
        # o modulo nem apaga o objeto 'mmu'.
        self._add_object('mmu_machine', _MmuMachine(self))
        # so cfs_1 (caso normal, 1 CFS): registrar cfs_2..4 criaria sensores
        # fantasma na lista de termicos do Fluidd. Caixas extras funcionam,
        # so nao mostram temp/umidade no rodape da unit.
        self._add_object('temperature_sensor cfs_1', _CfsSensor(self, 1))

        # comandos do painel do Fluidd -> BOX_* do CFS (cada um isolado)
        try:
            self.gcode = self.printer.lookup_object('gcode')
        except Exception:
            self.gcode = None
        self._reg('SET_MMU_BOXES', self.cmd_SET_MMU_BOXES,
                  "Quantas caixas CFS o painel mostra (BOXES=0 auto, 1..4)")
        self._reg('MMU_SELECT', self.cmd_MMU_SELECT, "Seleciona um gate (GATE=n)")
        self._reg('MMU_CHANGE_TOOL', self.cmd_MMU_CHANGE_TOOL,
                  "Carrega o slot do CFS (TOOL=n) via BOX_LOAD_MATERIAL")
        self._reg('MMU_LOAD', self.cmd_MMU_LOAD, "Carrega o gate selecionado")
        self._reg('MMU_UNLOAD', self.cmd_MMU_UNLOAD, "Descarrega (BOX_QUIT_MATERIAL)")
        self._reg('MMU_EJECT', self.cmd_MMU_UNLOAD, "Descarrega (BOX_QUIT_MATERIAL)")
        self._reg('MMU_GATE_MAP', self.cmd_MMU_GATE_MAP,
                  "Edita slots do CFS a partir do painel do Fluidd")
        # sem equivalente seguro no CFS a partir do Klipper: informam e param
        for cmd in ('MMU_PRELOAD', 'MMU_CHECK_GATE', 'MMU_CHECK_GATES',
                    'MMU_RECOVER', 'MMU_UNLOCK', 'MMU_STATS', 'MMU_SPOOLMAN',
                    'MMU_HOME'):
            self._reg(cmd, self._cmd_noop(cmd), "Sem equivalente no CFS")

    # ---- helpers de registro isolado ----
    def _add_object(self, nome, obj):
        try:
            self.printer.add_object(nome, obj)
        except Exception as err:
            logging.info("joelma mmu: '%s' nao registrado (%s)", nome, err)

    def _reg(self, nome, fn, desc):
        try:
            self.gcode.register_command(nome, fn, desc=desc)
        except Exception as err:
            logging.info("joelma mmu: comando %s nao registrado (%s)", nome, err)

    def _le_persist(self):
        try:
            with open(PERSIST) as f:
                v = int(json.load(f).get("num_boxes", 0))
            if 0 <= v <= 4:
                self.num_boxes = v
        except Exception:
            pass

    def _connect(self):
        try:
            self.box = self.printer.lookup_object('box')
        except Exception:
            self.box = None

    def _caixas(self, maxbox):
        return self.num_boxes if self.num_boxes > 0 else maxbox

    def _agora(self):
        try:
            return self.printer.get_reactor().monotonic()
        except Exception:
            return 0.0

    # ---- comandos ----
    def cmd_SET_MMU_BOXES(self, gcmd):
        v = gcmd.get_int('BOXES', 0, minval=0, maxval=4)
        self.num_boxes = v
        try:
            with open(PERSIST, "w") as f:
                json.dump({"num_boxes": v}, f)
        except Exception as err:
            gcmd.respond_info("aviso: nao persistiu (%s)" % err)
        gcmd.respond_info("Painel MMU: caixas CFS = %s" % ("auto" if v == 0 else v))

    def _gate_ocupado(self, g):
        gates, maxbox, _ = self._scan(self._agora())
        if g < 0 or g >= self._caixas(maxbox) * 4:
            return None
        return g in gates

    def cmd_MMU_SELECT(self, gcmd):
        g = gcmd.get_int('GATE', gcmd.get_int('TOOL', -1))
        self.sel_gate = g if 0 <= g <= 15 else -1
        gcmd.respond_info("MMU: gate %s (%s)" % (self.sel_gate, _tnn_do_gate(self.sel_gate))
                          if self.sel_gate >= 0 else "MMU: selecao limpa")

    def _carrega(self, gcmd, g):
        ocupado = self._gate_ocupado(g)
        if ocupado is None:
            raise gcmd.error("MMU: gate %d fora do painel" % g)
        if not ocupado:
            # carregar slot vazio faz BOX_EXTRUDE_MATERIAL estourar com None
            # dentro do blob da Creality e derruba o Klipper
            raise gcmd.error("MMU: slot %s vazio - nao vou carregar" % _tnn_do_gate(g))
        tnn = _tnn_do_gate(g)
        self.sel_gate = g
        gcmd.respond_info("MMU: carregando %s..." % tnn)
        self.gcode.run_script_from_command("BOX_LOAD_MATERIAL TNN=%s" % tnn)

    def cmd_MMU_CHANGE_TOOL(self, gcmd):
        self._carrega(gcmd, gcmd.get_int('TOOL', gcmd.get_int('GATE', -1)))

    def cmd_MMU_LOAD(self, gcmd):
        g = gcmd.get_int('GATE', self.sel_gate)
        if g < 0:
            raise gcmd.error("MMU: selecione um gate antes (MMU_SELECT GATE=n)")
        self._carrega(gcmd, g)

    def cmd_MMU_UNLOAD(self, gcmd):
        gcmd.respond_info("MMU: descarregando...")
        self.gcode.run_script_from_command("BOX_QUIT_MATERIAL")

    def _cmd_noop(self, nome):
        def handler(gcmd, _n=nome):
            gcmd.respond_info("%s: sem equivalente no CFS (edite pelo painel MMU "
                              "ou pela tela da impressora)" % _n)
        return handler

    # Editar slot pelo painel do Fluidd: MMU_GATE_MAP MAP="{0:{...},1:{...}}".
    # Grava no material_modify_info.json (overlay que este modulo LE) -> a cor
    # e o material aparecem no painel E no Orca ao vivo, sem tocar no 485.
    def cmd_MMU_GATE_MAP(self, gcmd):
        raw = gcmd.get('MAP', None)
        if not raw:
            gcmd.respond_info("MMU_GATE_MAP: nada a fazer (sem MAP)")
            return
        try:
            # o Fluidd manda dict estilo Python (aspas simples, chaves int)
            mapa = ast.literal_eval(raw)
        except Exception as err:
            gcmd.respond_info("MMU_GATE_MAP: MAP invalido (%s)" % err)
            return
        if not isinstance(mapa, dict):
            gcmd.respond_info("MMU_GATE_MAP: MAP nao e um dict")
            return
        aplicados = 0
        for gate, d in mapa.items():
            try:
                g = int(gate)
            except (TypeError, ValueError):
                continue
            if not isinstance(d, dict):
                continue
            tnn = _tnn_do_gate(g)
            base = _tipo_base(d.get('material') or '')
            cor = _norm_cor(d.get('color') or '')
            nome = str(d.get('name') or '').strip()
            temp = d.get('temp')
            try:
                temp = int(temp)
            except (TypeError, ValueError):
                temp = -1
            if self._grava_overlay(tnn, base, cor, nome, temp):
                aplicados += 1
        # invalida o cache do overlay para o proximo get_status ja refletir
        self._mod_cache = ({}, 0.0)
        gcmd.respond_info("MMU_GATE_MAP: %d slot(s) atualizado(s)" % aplicados)

    def _grava_overlay(self, tnn, base, cor, nome, temp):
        # atualiza (ou cria) a entrada do slot no material_modify_info.json
        if _gate_do_tnn(tnn) is None:
            return False
        box_id = "T" + tnn[1]
        slot_i = ord(tnn[2]) - ord("A")
        try:
            data = {}
            if os.path.isfile(MODIFY):
                with open(MODIFY) as f:
                    data = json.load(f)
            if not isinstance(data, dict):
                data = {}
            mats = data.setdefault("Material", [])
            caixa = next((c for c in mats if str(c.get("boxID", "")) == box_id), None)
            if caixa is None:
                caixa = {"boxID": box_id, "list": []}
                mats.append(caixa)
            lst = caixa.setdefault("list", [])
            while len(lst) <= slot_i:
                lst.append({})
            slot = lst[slot_i]
            vazio = not base or not cor
            if vazio:
                # slot esvaziado no painel -> desmarca a edicao (volta pro RFID)
                slot["editStatus"] = 0
            else:
                lo, hi = FAIXA_TEMP.get(base, (190, 260))
                if temp and temp > 0:
                    lo, hi = max(150, temp - 20), temp + 20
                slot.update({
                    "editStatus": 1,
                    "filamentId": FILAMENT_ID.get(base, "000001"),
                    "materialType": base,
                    "color": "#0" + cor.lower(),
                    "name": nome,
                    "brand": "",
                    "minTemp": lo, "maxTemp": hi,
                })
            with open(MODIFY, "w") as f:
                json.dump(data, f)
            return True
        except Exception as err:
            logging.warning("joelma mmu: overlay %s falhou (%s)", tnn, err)
            return False

    # ---- leitura do box ----
    def _edicoes(self, eventtime):
        cache, ts = self._mod_cache
        if eventtime - ts < 2.0:
            return cache
        edits = {}
        try:
            with open(MODIFY) as f:
                data = json.load(f)
            for caixa in data.get("Material", []):
                bx = str(caixa.get("boxID", "")).strip()
                for i, slot in enumerate(caixa.get("list", [])):
                    if i > 3:
                        break
                    if str(slot.get("editStatus", "")).strip() not in ("1", "1.0"):
                        continue
                    mt = (slot.get("materialType") or "").strip()
                    if not mt:
                        continue
                    nome = " ".join(x for x in [
                        str(slot.get("brand") or "").strip(),
                        str(slot.get("name") or "").strip()] if x)
                    temp = 0
                    try:
                        tmin = int(slot.get("minTemp") or 0)
                        tmax = int(slot.get("maxTemp") or 0)
                        if tmin and tmax:
                            temp = (tmin + tmax) // 2
                    except (TypeError, ValueError):
                        pass
                    edits[bx + chr(ord("A") + i)] = {
                        "mat": mt, "cor": _norm_cor(slot.get("color")),
                        "nome": nome, "temp": temp,
                    }
        except Exception:
            pass
        self._mod_cache = (edits, eventtime)
        return edits

    def _scan(self, eventtime):
        # (gates, maxbox, extras) com cache de 1s. extras[n]={temp,umid,versao}.
        g, mb, ex, ts = self._scan_cache
        if g is not None and eventtime - ts < 1.0:
            return g, mb, ex
        gates, maxbox, extras = {}, 0, {}
        try:
            bs = self.box.get_status(eventtime) if self.box else {}

            # schema K2 Plus: box.T1..T4
            for n in (1, 2, 3, 4):
                t = bs.get("T%d" % n)
                if not isinstance(t, dict):
                    continue
                mats = t.get("material_type")
                cores = t.get("color_value")
                if not isinstance(mats, (list, tuple)):
                    mats = []
                if not isinstance(cores, (list, tuple)):
                    cores = []
                ocupada = any(str(m).strip() not in ("-1", "", "None") for m in mats)
                st_box = str(t.get("state", "")).strip().lower()
                conectada = st_box in ("connect", "connected")
                # T1 SEMPRE aparece se existir (o sync nunca vai a zero). T2..T4
                # (encadeadas) so aparecem conectadas ou com filamento - evita
                # as caixas fantasma que o firmware publica vazias.
                if n != 1 and not conectada and not ocupada:
                    continue
                maxbox = max(maxbox, n)
                extras[n] = {
                    "temp": _num(t.get("temperature")),
                    "umid": _num(t.get("dry_and_humidity")),
                    "versao": str(t.get("version") or "").strip() or None,
                }
                restos = t.get("remain_len")
                if not isinstance(restos, (list, tuple)):
                    restos = []
                for i in range(4):
                    cod = str(mats[i]).strip() if i < len(mats) else "-1"
                    if cod in ("-1", "", "None"):
                        continue
                    nome, tipo = _material_do_codigo(cod)
                    resto = _num(restos[i] if i < len(restos) else None)
                    gates[(n - 1) * 4 + i] = {
                        "mat": tipo, "cor": _norm_cor(cores[i] if i < len(cores) else ""),
                        "nome": nome, "temp": 0,
                        "resto": int(resto) if resto is not None and 0 <= resto <= 100 else None,
                    }

            # fallback K1: same_material
            if not gates and not maxbox:
                for mat in bs.get("same_material") or []:
                    tipo = str(mat[3]) if len(mat) > 3 else "PLA"
                    cor = _norm_cor(mat[1] if len(mat) > 1 else "")
                    for tnn in (mat[2] if len(mat) > 2 and mat[2] else []):
                        gg = _gate_do_tnn(tnn)
                        if gg is None:
                            continue
                        gates[gg] = {"mat": tipo, "cor": cor, "nome": "",
                                     "temp": 0, "resto": None}
                        maxbox = max(maxbox, gg // 4 + 1)

            # overlay das edicoes (so em slot que o box diz ocupado)
            for tnn, ov in self._edicoes(eventtime).items():
                gg = _gate_do_tnn(tnn)
                if gg is not None and gg in gates:
                    for k, v in ov.items():
                        if v:
                            gates[gg][k] = v
        except Exception as err:
            logging.error("joelma mmu _scan: %s", err)

        self._scan_cache = (gates, maxbox, extras, eventtime)
        return gates, maxbox, extras

    def get_status(self, eventtime):
        # NUNCA levanta: em qualquer erro devolve um mmu vazio porem valido
        # (o painel fica "enabled" e o Orca nao quebra).
        try:
            gates, maxbox, _ = self._scan(eventtime)
            n = self._caixas(maxbox) * 4
        except Exception:
            gates, n = {}, 0
        status, material = [0] * n, [""] * n
        color, temp, nomes = [""] * n, [0] * n, [""] * n
        restos = [-1] * n
        for g, d in gates.items():
            if g >= n:
                continue
            base = _tipo_base(d.get("mat"))
            status[g] = 1
            material[g] = base
            color[g] = d.get("cor", "")
            temp[g] = d.get("temp") or TEMP_PADRAO.get(base, 220)
            nomes[g] = d.get("nome") or base
            if d.get("resto") is not None:
                nomes[g] += " ~%d%%" % d["resto"]
                restos[g] = d["resto"]
        return {
            # o que o OrcaSlicer le (fetch_hh_filament_info)
            'num_gates': n,
            'gate_status': status,
            'gate_material': material,
            'gate_color': color,
            'gate_temperature': temp,
            # estado que o painel MMU do Fluidd espera (so-leitura + acoes)
            'enabled': True,
            'print_state': 'ready',
            'action': 'Idle',
            'is_homed': True,
            'is_paused': False,
            'filament': 'Unloaded',
            'filament_pos': 0,
            'filament_position': 0.0,
            'tool': self.sel_gate,
            'gate': self.sel_gate,
            'unit': (self.sel_gate // 4) if self.sel_gate >= 0 else -1,
            'ttg_map': list(range(n)),
            'endless_spool_groups': list(range(n)),
            'gate_spool_id': [-1] * n,
            'gate_filament_name': nomes,
            'gate_speed_override': [100] * n,
            # extensao nao-padrao: % restante por gate (fork OrcaSlicer-K2-Wave)
            'gate_remain': restos,
            'boxes_config': self.num_boxes,
            'id': self.id,
        }


def load_config(config):
    return mmu(config)
