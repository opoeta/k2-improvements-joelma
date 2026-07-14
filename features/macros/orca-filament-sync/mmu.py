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

MODIFY = "/mnt/UDISK/creality/userdata/box/material_modify_info.json"

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


class mmu:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.id = config.getfloat("id", default=0.0)
        self.box = None
        self._mod_cache = ({}, 0.0)
        # o objeto box pode carregar depois deste; resolve no connect
        self.printer.register_event_handler("klippy:connect", self._connect)

    def _connect(self):
        try:
            self.box = self.printer.lookup_object('box')
        except Exception:
            self.box = None

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

    def get_status(self, eventtime):
        gates, maxbox = {}, 0
        try:
            bs = self.box.get_status(eventtime) if self.box else {}

            # caminho 1: schema da K2 Plus fw 1.1.6.x — box.T1..T4 por caixa
            # (caixa ausente vem como a string "None", por isso o isinstance)
            for n in (1, 2, 3, 4):
                t = bs.get("T%d" % n)
                if not isinstance(t, dict):
                    continue
                maxbox = max(maxbox, n)
                mats = t.get("material_type")
                cores = t.get("color_value")
                if not isinstance(mats, (list, tuple)):
                    mats = []
                if not isinstance(cores, (list, tuple)):
                    cores = []
                for i in range(4):
                    cod = str(mats[i]).strip() if i < len(mats) else "-1"
                    if cod in ("-1", "", "None"):
                        continue  # slot vazio
                    nome, tipo = _material_do_codigo(cod)
                    gates[(n - 1) * 4 + i] = {
                        "mat": tipo,
                        "cor": _norm_cor(cores[i] if i < len(cores) else ""),
                        "nome": nome,
                        "temp": 0,
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
                        gates[g] = {"mat": tipo, "cor": cor, "nome": "", "temp": 0}
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

        n = maxbox * 4
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
        return {
            # o que o OrcaSlicer le (MoonrakerPrinterAgent::fetch_hh_filament_info)
            'num_gates': n,
            'gate_status': status,
            'gate_material': material,
            'gate_color': color,
            'gate_temperature': temp,
            # extras que o painel MMU do Fluidd espera para nao aparecer
            # "(disabled)". O painel fica SO-LEITURA: os botoes dele chamam
            # macros MMU_* do Happy Hare que nao existem aqui.
            'enabled': True,
            'tool': -1,
            'gate': -1,
            'ttg_map': list(range(n)),
            'gate_spool_id': [-1] * n,
            'gate_filament_name': nomes,
            'id': self.id,
        }


def load_config(config):
    return mmu(config)
