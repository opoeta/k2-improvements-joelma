# Simula um MMU (Happy Hare) a partir do objeto 'box' do CFS, para o
# OrcaSlicer sincronizar cor/material dos slots via Moonraker.
#
# Baseado em Stevetm2/K2_Custom_Macros (K2OrcaFilamentSync), adaptado para a
# Joelma com uma diferenca-chave: alem do objeto box (RFID/hardware), o
# get_status SOBREPOE as edicoes gravadas em material_modify_info.json pelo
# componente joelma_cfs_edit. Assim, editar um slot na Central de Calibracao
# aparece no Orca AO VIVO — sem restart do Klipper e sem o protocolo 485.
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


def _norm_cor(c):
    # "0RRGGBB" ou "#0RRGGBB" -> "RRGGBB" (6 hex, sem # e sem o 0 da frente)
    if not c:
        return ""
    c = str(c).lstrip("#")
    if len(c) == 7 and c[0] == "0":
        c = c[1:]
    return c[-6:].upper()


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
                bx = caixa.get("boxID", "")
                for i, slot in enumerate(caixa.get("list", [])):
                    if i > 3:
                        break
                    tnn = bx + chr(ord("A") + i)
                    mt = (slot.get("materialType") or "").strip()
                    if mt:
                        edits[tnn] = {
                            "mat": mt,
                            "cor": _norm_cor(slot.get("color")),
                        }
        except Exception:
            pass
        self._mod_cache = (edits, eventtime)
        return edits

    def get_status(self, eventtime):
        status, material, color, temp = [], [], [], []
        try:
            same = self.box.get_status(eventtime)["same_material"] if self.box else []
            edits = self._edicoes(eventtime)
            for mat in same:
                # mat = [filamentId, "0RRGGBB", [TNN...], "PLA"]
                tnn = mat[2][0] if len(mat) > 2 and mat[2] else ""
                matType = mat[3] if len(mat) > 3 else "PLA"
                cor = _norm_cor(mat[1] if len(mat) > 1 else "")
                ov = edits.get(tnn)
                if ov:                       # edicao da Central manda
                    matType = ov["mat"] or matType
                    cor = ov["cor"] or cor
                status.append(1)
                material.append("PLA HIGH SPEED" if "PLA" in matType.upper() else matType)
                color.append(cor)
                temp.append(222 if "PLA" in matType.upper() else 245)
        except Exception as err:
            logging.error("joelma mmu get_status: %s", err)
        return {
            'num_gates': len(color),
            'gate_status': status,
            'gate_material': material,
            'gate_color': color,
            'gate_temperature': temp,
            'id': self.id,
        }


def load_config(config):
    return mmu(config)
