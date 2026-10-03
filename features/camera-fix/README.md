# camera-fix — Câmera no Fluidd (WebRTC)

A câmera stock do K2 (porta 8000) às vezes para de aparecer no Fluidd. Na nossa
Central (`calibra.html`) a câmera funciona; este fix leva o mesmo viewer WebRTC
pro Fluidd, servido em **`/usr/share/fluidd/camera.html`** → acesse em
`http://IP:4408/camera.html`. Viewer autossuficiente (token pela porta 9999 +
`/call/webrtc_local`). Portado de HurricanePrint/Creality-K2-Camera-Fix. Some
num update de firmware (é só um arquivo em /usr/share/fluidd).
