# WebSocket falso da porta 9999 (K2): responde get boxsInfo com o estado real
# do CFS do usuario, T1B alimentando (feedState 107) e erro 836.
import socket, threading, hashlib, base64, json, struct, sys
MODO = sys.argv[1] if len(sys.argv) > 1 else "troca"
if MODO == "sem": sys.exit(0)
def box(i, mats): return {"id": i, "type": 0, "state": 1, "temp": 31, "humidity": 38, "materials": mats}
def m(i, st, sel, tp, cor): return {"id": i, "state": st, "selected": sel, "type": tp, "color": cor, "name": tp, "editStatus": 1, "minTemp": 190, "maxTemp": 240}
INFO = {"materialBoxs": [
  box(1, [m(0,1,0,"PLA","#0ffffff"), m(1,3 if MODO=="troca" else 2,1,"PLA","#00a2989"), m(2,0,0,"","#0000000"), m(3,1,0,"PLA","#03ddf57")]),
  box(2, [m(0,1,0,"PLA","#0ff8b1f"), m(1,1,0,"PLA","#01b04ae"), m(2,1,0,"PLA","#0ba552a"), m(3,1,0,"PLA","#09cff4f")]),
  {"id": 0, "type": 1, "state": 0, "materials": [m(0,1,0,"PLA","#0ffffff")]}]}
def frame(txt):
    b = txt.encode(); h = bytearray([0x81])
    if len(b) < 126: h.append(len(b))
    elif len(b) < 65536: h.append(126); h += struct.pack(">H", len(b))
    else: h.append(127); h += struct.pack(">Q", len(b))
    return bytes(h) + b
def le(c):
    h = c.recv(2)
    if len(h) < 2: return None
    n = h[1] & 127
    if n == 126: n = struct.unpack(">H", c.recv(2))[0]
    elif n == 127: n = struct.unpack(">Q", c.recv(8))[0]
    mk = c.recv(4); d = bytearray(c.recv(n))
    for i in range(len(d)): d[i] ^= mk[i % 4]
    return (h[0] & 15, d.decode(errors="replace"))
def cliente(c):
    req = c.recv(4096).decode()
    k = [l.split(":",1)[1].strip() for l in req.split("\r\n") if l.lower().startswith("sec-websocket-key")][0]
    ac = base64.b64encode(hashlib.sha1((k + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
    c.send(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + ac + "\r\n\r\n").encode())
    c.send(frame('{"ModeCode":"heart_beat"}'))
    while True:
        f = le(c)
        if not f or f[0] == 8: break
        print("RECEBI:", f[1], flush=True)
        if '"get"' in f[1]:
            r = {"boxsInfo": INFO, "cfsConnect": 1, "state": 0}
            if MODO == "troca": r.update({"feedState": 107, "err": {"key": 836, "value": "extrude error, maybe there's a blockage between the connections and the filament sensor"}})
            else: r.update({"feedState": 0, "err": {"key": 0, "value": ""}})
            c.send(frame(json.dumps(r)))
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", 9999)); s.listen(5)
while True:
    c, _ = s.accept(); threading.Thread(target=cliente, args=(c,), daemon=True).start()
