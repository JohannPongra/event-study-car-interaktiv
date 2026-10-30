"""oberflaeche · server – klar abgegrenzter Projektbaustein."""
from Programm.oberflaeche.routen import Handler
from http.server import ThreadingHTTPServer
import webbrowser

def starten(port=8766, browser=True):
    if not 1024 <= port <= 65535:
        raise ValueError('Port muss zwischen 1024 und 65535 liegen.')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    except OSError:
        raise ValueError('Port belegt. Vorherige Oberfläche schließen oder python -m Programm oberflaeche --port 8767 verwenden.') from None
    url = f'http://127.0.0.1:{port}'
    print('Event Study Final: ' + url)
    print('Dieses Fenster offen lassen. Beenden mit Strg+C.')
    if browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Oberfläche beendet.')
    finally:
        server.server_close()
