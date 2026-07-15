# Simula um MMU (Happy Hare) a partir do objeto 'box' do CFS, para o
# OrcaSlicer sincronizar cor/material dos slots via Moonraker.
#
# Baseado em Stevetm2/K2_Custom_Macros (K2OrcaFilamentSync), adaptado para a
# Joelma com tres diferencas-chave:
#   1. Le o objeto box nos DOIS schemas conhecidos:
#      - K2 Plus fw 1.1.6.x (o schema REAL da Joelma, handoff secao 4):
#        box.T1..T4 = {"material_type": [...], "color_value": [...], ...}
#        O original lia so 'same_material', que aqui nao existe — os gates
#        vinham vazios e o Fluidd mostrava "Mmu (disabled)" sem slots.
#      - Fallback (schema K1/Stevetm2): box.same_material =
#        [[filamentId, "0RRGGBB", ["T1A", ...], "PLA"], ...], expandindo
#        TODOS os TNN de cada grupo — o original pegava so o primeiro TNN
#        e colapsava slots do mesmo material num gate unico.
#   2. Gates indexados pela POSICAO FISICA: gate = (caixa-1)*4 + slot
#      (T1A=0 ... T1D=3, T2A=4, ...), como o Orca e o Fluidd esperam.
#      gate_material publica o TIPO BASE (PLA/PETG/ABS/...) porque o Orca
#      resolve o preset com filament_id_by_type(tipo) — nome de produto ali
#      quebra o match e cai no generico.
#   3. get_status SOBREPOE as edicoes gravadas em material_modify_info.json
#      pelo componente joelma_cfs_edit. Assim, editar um slot na Central de
#      Calibracao aparece no Orca AO VIVO — sem restart e sem protocolo 485.
#
# O Klipper carrega este arquivo por causa da secao [mmu] (o nome do arquivo
# TEM que ser mmu.py e a secao [mmu], que e o objeto que o Orca procura).
#
# Defensivo: get_status NUNCA levanta excecao — se o box sumir ou o JSON
# estiver ausente, devolve gates vazios. O Klipper nunca cai por causa disto.
#
# GPLv3 (herdado do original).
import json
import logging
import os

MODIFY = "/mnt/UDISK/creality/userdata/box/material_modify_info.json"
# override persistido do SET_MMU_BOXES (0 = auto-detectar pelas caixas
# conectadas; 1..4 = forca a quantidade de CFS no painel)
PERSIST = os.path.expanduser("~/printer_data/config/.joelma_mmu.json")

# Codigos de 6 digitos que ESTA impressora usa nos slots sem RFID e nos
# editados pela Central (mesma tabela FILAMENT_ID do joelma_cfs_edit.py —
# as duas andam SEMPRE juntas). Consultada ANTES do catalogo: "002001" aqui
# e PETG, mas os 5 digitos finais ("02001") no catalogo seriam Hyper PLA-CF.
TIPO_LOCAL = {
    "000001": "PLA", "002001": "PETG", "003001": "ABS", "004001": "TPU",
    "005001": "ASA", "006001": "PA", "007001": "PC",
}

# Catalogo Creality (material_database.json da impressora; espelhado pelos
# projetos K2-RFID e sandman21vs/OrcaSlicer-k1c-cfs). Spool COM RFID reporta
# um filamentId com prefixo de serie + estes 5 digitos finais.
# codigo -> (nome do produto, tipo base)
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

# temperatura de bico padrao por tipo (gate_temperature quando a edicao da
# Central nao definiu faixa)
TEMP_PADRAO = {
    "PLA": 220, "PETG": 240, "ABS": 260, "ASA": 260, "TPU": 230,
    "PA": 270, "PC": 270, "PVA": 220, "HIPS": 250, "PET": 260,
}

# tipos que o Orca conhece de fabrica (passam direto); o resto e reduzido ao
# prefixo base para o filament_id_by_type nao falhar
TIPOS_ORCA = {
    "PLA", "PLA-CF", "PETG", "PETG-CF", "PETG-GF", "PET", "PET-CF", "ABS",
    "ASA", "ASA-CF", "TPU", "PC", "PA", "PA-CF", "PA-GF", "PVA", "HIPS",
    "PP", "PP-CF", "PPS", "PPS-CF", "PCTG", "BVOH",
}


def _num(v):
    # "21" -> 21.0; "-1"/""/None/"None" -> None
    try:
        f = float(str(v).strip())
        return f if f >= 0 else None
    except (TypeError, ValueError):
        return None


def _tnn_do_gate(g):
    # 0 -> "T1A", 5 -> "T2B"
    return "T%d%s" % (g // 4 + 1, "ABCD"[g % 4])


def _norm_cor(c):
    # "0RRGGBB" ou "#0RRGGBB" -> "RRGGBB" (6 hex, sem # e sem o 0 da frente)
    if not c:
        return ""
    c = str(c).lstrip("#")
    if len(c) == 7 and c[0] == "0":
        c = c[1:]
    return c[-6:].upper()


def _gate_do_tnn(tnn):
    # "T1A" -> 0, "T1D" -> 3, "T2A" -> 4 ... None se invalido
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
    # ordem importa: PETG antes de PET antes de PLA; PA por ultimo
    for b in ("PETG", "PET", "PLA", "ABS", "ASA", "TPU", "PVA", "HIPS", "PC", "PA"):
        if t.startswith(b):
            return b
    return t or "PLA"


def _material_do_codigo(cod):
    # filamentId -> (nome, tipo). Tabela local (6 digitos) primeiro, depois o
    # catalogo pelos 5 digitos finais (spools com RFID), senao PLA generico.
    cod = str(cod or "").strip()
    if cod in TIPO_LOCAL:
        t = TIPO_LOCAL[cod]
        return t, t
    ent = CATALOGO.get(cod) or (CATALOGO.get(cod[-5:]) if len(cod) >= 5 else None)
    if ent:
        return ent[0], ent[1]
    return "", "PLA"


# O Fluidd le as unidades/gates de um SEGUNDO objeto, 'mmu_machine'
# (mixins/mmu.ts: numGates cai no default 1 sem ele — dai o painel mostrar
# 1 spool fantasma). Publica 1 unit por caixa do CFS, 4 gates cada.
# environment_sensor aponta pro _CfsSensor abaixo: o rodape da unit no
# Fluidd mostra a temperatura/umidade do CFS (o que o card da Central
# mostrava); version = firmware real da caixa (box.Tn.version).
class _MmuMachine:
    def __init__(self, dono):
        self.dono = dono

    def get_status(self, eventtime):
        _, maxbox, extras = self.dono._scan(eventtime)
        maxbox = self.dono._caixas(maxbox)
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


# Sensor fake com a temperatura/umidade do CFS (box.Tn.temperature e
# .dry_and_humidity). Aparece no rodape da unit do painel MMU e tambem
# na lista de sensores/termicos do Fluidd.
class _CfsSensor:
    def __init__(self, dono, caixa):
        self.dono, self.caixa = dono, caixa

    def get_status(self, eventtime):
        _, _, extras = self.dono._scan(eventtime)
        info = extras.get(self.caixa, {})
        return {
            'temperature': info.get('temp') or 0.0,
            'humidity': info.get('umid') or 0.0,
        }


class mmu:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.id = config.getfloat("id", default=0.0)
        # quantidade de CFS no painel: 0 = auto (caixas conectadas);
        # o arquivo persistido pelo SET_MMU_BOXES tem precedencia sobre o cfg
        self.num_boxes = config.getint("num_boxes", 0, minval=0, maxval=4)
        self._le_persist()
        self.box = None
        self.sel_gate = -1     # gate selecionado via MMU_SELECT (so visual)
        self._mod_cache = ({}, 0.0)
        self._scan_cache = (None, None, None, -1.0)
        # o objeto box pode carregar depois deste; resolve no connect
        self.printer.register_event_handler("klippy:connect", self._connect)
        # registra o mmu_machine junto (o Fluidd precisa dos dois)
        try:
            self.printer.add_object('mmu_machine', _MmuMachine(self))
        except Exception:
            pass  # ja existe (Happy Hare real?) — nao briga
        # configurador: SET_MMU_BOXES BOXES=0..4 (0 = auto), persiste e
        # aplica ao vivo — a Central chama isto no seletor do card CFS.
        # E os comandos MMU_* que os botoes do painel do Fluidd disparam,
        # mapeados pros BOX_* do CFS (com guarda de slot vazio: mandar
        # BOX_LOAD_MATERIAL num slot sem filamento derruba o Klipper —
        # visto ao vivo jul/2026, mesma guarda que a Central usava).
        self.gcode = None
        try:
            self.gcode = self.printer.lookup_object('gcode')
            reg = self.gcode.register_command
            reg('SET_MMU_BOXES', self.cmd_SET_MMU_BOXES,
                desc="Define quantas caixas CFS o painel MMU mostra (BOXES=0 auto, 1..4)")
            reg('MMU_SELECT', self.cmd_MMU_SELECT,
                desc="Seleciona um gate (GATE=n) — so visual no CFS")
            reg('MMU_CHANGE_TOOL', self.cmd_MMU_CHANGE_TOOL,
                desc="Carrega o slot do CFS (TOOL=n) via BOX_LOAD_MATERIAL")
            reg('MMU_LOAD', self.cmd_MMU_LOAD,
                desc="Carrega o gate selecionado via BOX_LOAD_MATERIAL")
            reg('MMU_UNLOAD', self.cmd_MMU_UNLOAD,
                desc="Descarrega o material atual via BOX_QUIT_MATERIAL")
            reg('MMU_EJECT', self.cmd_MMU_UNLOAD,
                desc="Descarrega o material atual via BOX_QUIT_MATERIAL")
            # sem equivalente seguro no CFS: responde orientacao e nao faz nada
            for cmd in ('MMU_PRELOAD', 'MMU_CHECK_GATE', 'MMU_CHECK_GATES',
                        'MMU_RECOVER', 'MMU_UNLOCK', 'MMU_STATS',
                        'MMU_SPOOLMAN', 'MMU_GATE_MAP', 'MMU_HOME'):
                reg(cmd, self._cmd_noop(cmd),
                    desc="Sem equivalente no CFS — nao faz nada")
        except Exception as err:
            logging.warning("joelma mmu: comandos nao registrados (%s)", err)

    def _le_persist(self):
        try:
            with open(PERSIST) as f:
                v = int(json.load(f).get("num_boxes", 0))
            if 0 <= v <= 4:
                self.num_boxes = v
        except Exception:
            pass

    def cmd_SET_MMU_BOXES(self, gcmd):
        v = gcmd.get_int('BOXES', 0, minval=0, maxval=4)
        self.num_boxes = v
        try:
            with open(PERSIST, "w") as f:
                json.dump({"num_boxes": v}, f)
        except Exception as err:
            gcmd.respond_info("aviso: nao consegui persistir (%s)" % err)
        gcmd.respond_info(
            "Painel MMU: caixas CFS = %s" % ("auto" if v == 0 else v))

    def _caixas(self, maxbox):
        # quantidade EFETIVA de caixas no painel (override > auto-detectado)
        return self.num_boxes if self.num_boxes > 0 else maxbox

    # ---- comandos MMU_* (botoes do painel do Fluidd) -> BOX_* do CFS ----

    def _agora(self):
        return self.printer.get_reactor().monotonic()

    def _gate_ocupado(self, g):
        gates, maxbox, _ = self._scan(self._agora())
        if g < 0 or g >= self._caixas(maxbox) * 4:
            return None       # fora do painel
        return g in gates     # True = tem filamento fisico

    def cmd_MMU_SELECT(self, gcmd):
        g = gcmd.get_int('GATE', gcmd.get_int('TOOL', -1))
        self.sel_gate = g if 0 <= g <= 15 else -1
        gcmd.respond_info("MMU: gate %s selecionado (%s)"
                          % (self.sel_gate, _tnn_do_gate(self.sel_gate))
                          if self.sel_gate >= 0 else "MMU: selecao limpa")

    def _carrega(self, gcmd, g):
        ocupado = self._gate_ocupado(g)
        if ocupado is None:
            raise gcmd.error("MMU: gate %d fora do painel" % g)
        if not ocupado:
            # NUNCA carregar slot vazio: BOX_EXTRUDE_MATERIAL estoura com
            # None dentro do blob da Creality e derruba o Klipper
            raise gcmd.error("MMU: slot %s sem filamento fisico — nao vou carregar"
                             % _tnn_do_gate(g))
        tnn = _tnn_do_gate(g)
        self.sel_gate = g
        gcmd.respond_info("MMU: carregando %s (aquece, corta, purga)..." % tnn)
        self.gcode.run_script_from_command("BOX_LOAD_MATERIAL TNN=%s" % tnn)

    def cmd_MMU_CHANGE_TOOL(self, gcmd):
        self._carrega(gcmd, gcmd.get_int('TOOL', gcmd.get_int('GATE', -1)))

    def cmd_MMU_LOAD(self, gcmd):
        g = gcmd.get_int('GATE', self.sel_gate)
        if g < 0:
            raise gcmd.error("MMU: selecione um gate antes (MMU_SELECT GATE=n)")
        self._carrega(gcmd, g)

    def cmd_MMU_UNLOAD(self, gcmd):
        gcmd.respond_info("MMU: descarregando material atual...")
        self.gcode.run_script_from_command("BOX_QUIT_MATERIAL")

    def _cmd_noop(self, nome):
        def handler(gcmd, _n=nome):
            gcmd.respond_info(
                "%s: sem equivalente no CFS (use a Central de Calibracao "
                "para editar slots / reler RFID)" % _n)
        return handler

    def _connect(self):
        try:
            self.box = self.printer.lookup_object('box')
        except Exception:
            self.box = None
        # sensores de temp/umidade das caixas detectadas (cfs_1 sempre:
        # e o caso normal e o rodape da unit 0 aponta pra ele)
        try:
            _, maxbox, _ = self._scan(self.printer.get_reactor().monotonic())
            for n in range(1, max(1, maxbox) + 1):
                try:
                    self.printer.add_object(
                        'temperature_sensor cfs_%d' % n, _CfsSensor(self, n))
                except Exception:
                    pass  # ja registrado
        except Exception as err:
            logging.warning("joelma mmu: sensores do CFS nao registrados (%s)", err)

    def _edicoes(self, eventtime):
        # cache de 2s: o get_status e chamado varias vezes por segundo
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
                    # so o que a Central editou de fato (o arquivo espelha
                    # todos os slots; sem este filtro, dado velho do espelho
                    # atropelaria um spool RFID trocado depois)
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
                        "mat": mt,
                        "cor": _norm_cor(slot.get("color")),
                        "nome": nome,
                        "temp": temp,
                    }
        except Exception:
            pass
        self._mod_cache = (edits, eventtime)
        return edits

    def _scan(self, eventtime):
        # varre o box + edicoes e devolve (gates, maxbox, extras). Cache de
        # 1s: o get_status (mmu, mmu_machine e sensores) e chamado varias
        # vezes/segundo. extras[n] = {temp, umid, versao} da caixa n.
        g, mb, ex, ts = self._scan_cache
        if g is not None and eventtime - ts < 1.0:
            return g, mb, ex
        gates, maxbox, extras = {}, 0, {}
        try:
            bs = self.box.get_status(eventtime) if self.box else {}

            # caminho 1: schema da K2 Plus fw 1.1.6.x — box.T1..T4 por caixa
            # (caixa ausente vem como a string "None", por isso o isinstance)
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
                # o firmware publica T2..T4 como dict mesmo SEM a caixa
                # (visto ao vivo na Joelma: 4 units fantasma no Fluidd) —
                # so conta caixa com state "connect" ou com slot ocupado
                st_box = str(t.get("state", "connect")).strip().lower()
                ocupada = any(
                    str(m).strip() not in ("-1", "", "None") for m in mats)
                if st_box not in ("connect", "connected") and not ocupada:
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
                        continue  # slot vazio
                    nome, tipo = _material_do_codigo(cod)
                    resto = _num(restos[i] if i < len(restos) else None)
                    gates[(n - 1) * 4 + i] = {
                        "mat": tipo,
                        "cor": _norm_cor(cores[i] if i < len(cores) else ""),
                        "nome": nome,
                        "temp": 0,
                        "resto": int(resto) if resto is not None and 0 <= resto <= 100 else None,
                    }

            # caminho 2 (fallback, schema K1/Stevetm2): same_material,
            # expandindo TODOS os TNN de cada grupo de material
            if not gates and not maxbox:
                for mat in bs.get("same_material") or []:
                    # mat = [filamentId, "0RRGGBB", [TNN...], "PLA"]
                    tipo = str(mat[3]) if len(mat) > 3 else "PLA"
                    cor = _norm_cor(mat[1] if len(mat) > 1 else "")
                    for tnn in (mat[2] if len(mat) > 2 and mat[2] else []):
                        g = _gate_do_tnn(tnn)
                        if g is None:
                            continue
                        gates[g] = {"mat": tipo, "cor": cor, "nome": "",
                                    "temp": 0, "resto": None}
                        maxbox = max(maxbox, g // 4 + 1)

            # edicao da Central manda (so em slot que o box diz ocupado)
            for tnn, ov in self._edicoes(eventtime).items():
                g = _gate_do_tnn(tnn)
                if g is not None and g in gates:
                    for k, v in ov.items():
                        if v:
                            gates[g][k] = v
        except Exception as err:
            logging.error("joelma mmu get_status: %s", err)

        self._scan_cache = (gates, maxbox, extras, eventtime)
        return gates, maxbox, extras

    def get_status(self, eventtime):
        gates, maxbox, _ = self._scan(eventtime)
        n = self._caixas(maxbox) * 4
        status, material = [0] * n, [""] * n
        color, temp, nomes = [""] * n, [0] * n, [""] * n
        for g, d in gates.items():
            if g >= n:
                continue
            base = _tipo_base(d["mat"])
            status[g] = 1
            material[g] = base
            color[g] = d["cor"]
            temp[g] = d.get("temp") or TEMP_PADRAO.get(base, 220)
            nomes[g] = d.get("nome") or base
            # % restante do slot (remain_len do box) visivel no painel
            if d.get("resto") is not None:
                nomes[g] += " ~%d%%" % d["resto"]
        return {
            # o que o OrcaSlicer le (MoonrakerPrinterAgent::fetch_hh_filament_info)
            'num_gates': n,
            'gate_status': status,
            'gate_material': material,
            'gate_color': color,
            'gate_temperature': temp,
            # extras que o painel MMU do Fluidd espera para nao aparecer
            # "(disabled)" nem quebrar o layout. O painel fica SO-LEITURA:
            # os botoes dele chamam macros MMU_* do Happy Hare que nao
            # existem aqui.
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
            # config atual do SET_MMU_BOXES (0 = auto) — a Central le isto
            # pra preencher o seletor; o Fluidd ignora chaves desconhecidas
            'boxes_config': self.num_boxes,
            'id': self.id,
        }


def load_config(config):
    return mmu(config)
