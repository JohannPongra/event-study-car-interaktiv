"""oberflaeche · routen – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import ROOT, pfad
from http.server import BaseHTTPRequestHandler
from Programm.oberflaeche.auftraege import JOB
from Programm.oberflaeche.auftraege import LOCK
from Programm.grundlagen.pfade import ORDNER
from Programm.oberflaeche.auftraege import TOKEN
from Programm.oberflaeche.auftraege import ausfuehren
from Programm.grundlagen.konfiguration import einstellungen
import json
from Programm.grundlagen.json_dateien import json_sicher
import mimetypes
import secrets
from Programm.grundlagen.json_dateien import speichern
import threading
from urllib.parse import urlsplit, unquote
from Programm.grundlagen.laufkennungen import zeit
from Programm.oberflaeche.zustand import zustand
WEB = pfad(ROOT, 'Programm/oberflaeche/web')

class Handler(BaseHTTPRequestHandler):

    def log_message(self, *_):
        pass

    def antwort(self, status, content, kind='application/json; charset=utf-8'):
        content = content if isinstance(content, bytes) else json.dumps(json_sicher(content), ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.end_headers()
        self.wfile.write(content)

    def host_ok(self):
        port = self.server.server_address[1]
        return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

    def do_GET(self):
        if not self.host_ok():
            return self.antwort(403, {'message': 'Nur lokal erreichbar.'})
        path = unquote(urlsplit(self.path).path)
        try:
            if path == '/api/state':
                return self.antwort(200, zustand())
            if path in {'/', '/app.js', '/style.css'}:
                file = pfad(WEB, 'index.html' if path == '/' else path[1:])
            elif path in {'/README.md', '/README.html', '/README_Technische_Details.md', '/METHODIK.md', '/PYTHON_KOMPATIBILITAET.md', '/ZUSAMMENSTELLUNG.md', '/Pruefbericht.md', '/KONTEXT_SENTIMENT.md'}:
                file = pfad(ORDNER, path[1:])
            elif path.startswith('/Anleitung_Grafiken/'):
                file = pfad(ORDNER, path[1:]).resolve()
                if pfad(ORDNER, 'Anleitung_Grafiken').resolve() not in file.parents:
                    return self.antwort(403, {'message': 'Dateipfad nicht zulässig.'})
            elif path.startswith('/dateien/'):
                file = pfad(pfad(ORDNER, 'Daten'), path.removeprefix('/dateien/')).resolve()
                if not any(((ORDNER / name).resolve() in file.parents for name in ['Daten', 'Ergebnisse', 'Archiv/Referenzbestand', 'Archiv/Referenzlauf'])):
                    return self.antwort(403, {'message': 'Dateipfad nicht zulässig.'})
            else:
                return self.antwort(404, {'message': 'Nicht gefunden.'})
            if not file.is_file():
                return self.antwort(404, {'message': 'Datei noch nicht erstellt.'})
            kind = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            if file.suffix == '.md':
                kind = 'text/plain; charset=utf-8'
            return self.antwort(200, file.read_bytes(), kind)
        except (ValueError, OSError, KeyError):
            return self.antwort(400, {'message': 'Datei/Einstellungen konnten nicht gelesen werden.'})

    def do_POST(self):
        if not self.host_ok() or not secrets.compare_digest(self.headers.get('X-Event-Token', ''), TOKEN):
            return self.antwort(403, {'message': 'Oberfläche neu laden.'})
        port = self.server.server_address[1]
        if self.headers.get('Origin') not in {f'http://127.0.0.1:{port}', f'http://localhost:{port}'}:
            return self.antwort(403, {'message': 'Nur aus der lokalen Oberfläche aufrufen.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('Ungültige Anfragegröße.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Anfrage muss ein JSON-Objekt sein.')
            cfg = einstellungen(payload.get('config', {}))
            with LOCK:
                if JOB['status'] == 'running':
                    return self.antwort(409, {'message': 'Der laufende Arbeitsschritt muss zuerst fertig werden.'})
                path = urlsplit(self.path).path
                if path == '/api/config':
                    speichern(pfad(ORDNER, 'einstellungen.json'), cfg)
                    return self.antwort(200, {'saved': True})
                if path != '/api/job' or payload.get('action') not in {'import', 'download', 'resume', 'process', 'finbert', 'calculate', 'regression', 'all', 'sentiment_compare'}:
                    raise ValueError('Unbekannter Arbeitsschritt.')
                key_values = payload.get('keys', {})
                if not isinstance(key_values, dict) or not set(key_values) <= {'alpha_vantage', 'serpapi'} or any((not isinstance(v, str) or len(v) > 500 for v in key_values.values())):
                    raise ValueError('Ungültige API-Schlüsselangaben.')
                speichern(pfad(ORDNER, 'einstellungen.json'), cfg)
                JOB.update(status='running', action=payload['action'], messages=[], result=None, started_at=zeit())
                threading.Thread(target=ausfuehren, args=(payload['action'], cfg, payload), daemon=True).start()
                return self.antwort(202, {'started': True})
        except (ValueError, TypeError, KeyError, OSError) as exc:
            return self.antwort(400, {'message': str(exc)[:500]})
