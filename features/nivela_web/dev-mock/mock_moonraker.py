# Moonraker falso: simula impressao em andamento (PLA / High Temp Plate)
import json, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
ST = {"off": 0.09, "vars": {"cur_placa":"high_temp_plate","cur_mat":"pla",
       "placa_high_temp_plate":"High Temp Plate","zoff_pla_high_temp_plate":0.09}}
def status(objs):
    base = {
      "print_stats":{"state":"printing","filename":"retraction_PLA.gcode"},
      "box":{"T1":{"vender":["unknown","3A9250276A210100100A29890165000001000000","-1","unknown"],"remain_len":["0","16","-1","0"],"color_value":["0ffffff","00A2989","0000000","03ddf57"],"material_type":["000001","101001","001601","000002"],"temperature":"31","dry_and_humidity":"38"},
             "T2":{"vender":["unknown","unknown","unknown","unknown"],"remain_len":["0","0","0","0"],"color_value":["0ff8b1f","01b04ae","0ba552a","09cff4f"],"material_type":["000001","000002","000001","000002"],"temperature":"30","dry_and_humidity":"41"},
             "same_material":[["001601","0000000",["T1C"],"PLA"],["101001","00A2989",["T1B"],"Hyper PLA"],["000001","0ffffff",["T1A","T2A","T2C"],"PLA"],["000002","03ddf57",["T1D","T2B","T2D"],"PETG"]]},
      "gcode_move":{"homing_origin":[0,0,round(ST["off"],3),0]},
      "save_variables":{"variables":ST["vars"]},
      "heater_bed":{"temperature":60.1,"target":60},
      "temperature_sensor chamber_temp":{"temperature":32.4},"temperature_sensor mcu_temp":{"temperature":38.3},"heater_fan hotend_fan":{"speed":1.0},"extruder":{"temperature":219.8,"target":220,"pressure_advance":0.04},
      "toolhead":{"position":[160.2,170.4,0.2,0],"homed_axes":"xyz","max_accel":5000,"square_corner_velocity":5},
      "idle_timeout":{"state":"Printing"},
      "display_status":{"message":"Imprimindo 1a camada"},
      "configfile":{"settings":{"extruder":{"rotation_distance":6.9},"input_shaper":{"shaper_type_x":"ei","shaper_freq_x":38.6,"shaper_type_y":"mzv","shaper_freq_y":40.6}}},
    }
    return {k: base.get(k, {}) for k in objs}
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _send(self, obj, code=200):
        b=json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self._send({})
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=="/printer/info": return self._send({"result":{"state":"ready","state_message":"ok"}})
        if u.path=="/printer/objects/query":
            objs=[k for k in parse_qs(u.query, keep_blank_values=True).keys()]
            return self._send({"result":{"status":status(objs),"eventtime":1}})
        if u.path=="/printer/objects/list":
            return self._send({"result":{"objects":["heater_bed","extruder","temperature_sensor chamber_temp","temperature_sensor mcu_temp","heater_fan hotend_fan","toolhead","gcode_move","print_stats","save_variables"]}})
        if u.path=="/server/gcode_store": return self._send({"result":{"gcode_store":[]}})
        if u.path=="/server/files/list":
            import os
            return self._send({"result":[{"path":f,"modified":os.path.getmtime("gcodes/"+f),"size":os.path.getsize("gcodes/"+f)} for f in os.listdir("gcodes")]})
        if u.path.startswith("/server/files/gcodes/"):
            from urllib.parse import unquote
            b=open("gcodes/"+unquote(u.path[len("/server/files/gcodes/"):]),"rb").read()
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("Access-Control-Expose-Headers","Content-Length")
            self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path=="/server/info": return self._send({"result":{"klippy_state":"ready"}})
        return self._send({"error":{"message":"not found"}},404)
    def do_POST(self):
        n=int(self.headers.get("Content-Length") or 0); body=self.rfile.read(n) if n else b"{}"
        u=urlparse(self.path)
        if u.path=="/printer/gcode/script":
            sc=json.loads(body or b"{}").get("script","")
            m=re.search(r"Z_ADJUST=(-?[\d.]+)",sc)
            if m: ST["off"]+=float(m.group(1))
            m=re.search(r"SAVE_VARIABLE VARIABLE=(\S+) VALUE=(\S+)",sc)
            if m: ST["vars"][m.group(1)]=(None if m.group(2)=="None" else float(m.group(2)))
            print("GCODE:",sc,flush=True)
            return self._send({"result":"ok"})
        return self._send({"error":{"message":"not found"}},404)
ThreadingHTTPServer(("127.0.0.1",7125),H).serve_forever()
