# virtual-sdcard-guard — Fix do "Unknown command" após o print

O upload da Creality às vezes anexa o delimitador HTTP multipart no fim do G-code
gravado; o Klipper tenta executar essa linha e reporta `Unknown command` depois do
print terminar. Este patch no `virtual_sdcard.py` (idempotente, fail-open) ignora
essa linha final só quando o conjunto de condições do delimitador bate. Portado de Rcpilot33.
