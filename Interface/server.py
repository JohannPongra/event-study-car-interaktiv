"""Lokale Bedienoberfläche; nur auf diesem Computer erreichbar."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import date, datetime
from urllib.parse import urlsplit, unquote
import argparse
import hashlib
import json
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
APP_ID = hashlib.sha256(str(ROOT).encode()).hexdigest()[:20]
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
JOB = {'status': 'idle', 'messages': [], 'result': None, 'action': ''}
RUNTIME = ROOT / '.venv/Scripts/python.exe'
DATASETS = ROOT / 'Daten/Arbeitsbestaende'
RUNS = ROOT / 'Ergebnisse/Analysen'
STATUS = ROOT / 'Interface/server-info.json'
ALLOWED = {'reference', 'download', 'resume', 'prepare', 'analyse', 'timings', 'install'}


def read_json(file, default=None):
    return json.loads(file.read_text(encoding='utf-8-sig')) if file.exists() else default


def dataset_config(name):
    if not isinstance(name, str) or not re.fullmatch(r'bestand_\d{8}_\d{6}_[a-f0-9]{6}', name):
        raise ValueError('Einen gültigen Datenbestand auswählen.')
    meta = read_json(DATASETS / name / 'bestand.json')
    if not meta or meta['art'] != 'download':
        raise ValueError('Dieser Bestand ist kein neuer Downloadbestand.')
    return meta['config']


def config_for(payload):
    from Programm.grundlagen.konfiguration import einstellungen
    action = payload['action']
    options = payload.get('options', {})
    if not isinstance(options, dict):
        raise ValueError('Ungültige Einstellungen.')
    if action == 'download':
        cfg = einstellungen()
        cfg.update(bestand='', return_type='simple', download_transcripts=True,
                   download_trends=True, predictors=['sue', 'vol', 'prevol', 'search', 'tone'])
        for key in ['tickers', 'start', 'end']:
            cfg[key] = options[key]
        if not set(cfg['tickers']) <= {'AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT'}:
            raise ValueError('Die Oberfläche verwendet die fünf Unternehmen der Arbeit.')
        if date.fromisoformat(cfg['end']) > date.today():
            raise ValueError('Das Enddatum darf nicht in der Zukunft liegen.')
    else:
        cfg = dict(dataset_config(payload.get('dataset')))
    if action in {'download', 'resume'}:
        cfg['request_limit'] = int(options.get('request_limit', 25))
        cfg['pause_seconds'] = float(options.get('pause_seconds', 12.5))
    return einstellungen(cfg)


def state():
    stocks = []
    for file in sorted(DATASETS.glob('bestand_*/bestand.json'), reverse=True):
        meta = read_json(file)
        if meta.get('art') != 'download':
            continue
        folder = file.parent
        status = read_json(folder / 'Nachweise/download_status.json', {})
        cfg = meta['config']
        stocks.append({'id': folder.name, 'status': status.get('status', 'incomplete'),
                       'label': f"{cfg['start']} – {cfg['end']} · {', '.join(cfg['tickers'])} · {meta['created_at'][:19].replace('T', ' ')}",
                       'start': cfg['start'], 'end': cfg['end']})
    runs = [{'id': 'reference', 'label': 'Seminararbeit · geprüfte Ausgangsdaten',
             'report': '/Ergebnisse/Ergebnisse.md',
             'figures': [f for f in read_json(ROOT / 'Interface/Abbildungen.json')['figures']
                         if f['source'] == 'calculated']}]
    for file in sorted(RUNS.glob('analyse_*/manifest.json'), reverse=True):
        meta = read_json(file)
        folder = file.parent
        figures = []
        from Interface.erstellen import berechnete_grafiken
        titles = {Path(f['image']).stem: f for f in berechnete_grafiken()}
        for image in sorted((folder / 'Grafiken').glob('*.png')):
            known = titles.get(image.stem, {})
            base = '/Ergebnisse/Analysen/' + folder.name + '/Grafiken/'
            figures.append({'id': folder.name + '_' + image.stem, 'source': 'calculated',
                            'title': known.get('title', image.stem),
                            'caption': known.get('title', image.stem),
                            'category': known.get('category', 'Überblick'),
                            'image': base + image.name, 'pdf': base + image.with_suffix('.pdf').name})
        runs.append({'id': folder.name, 'label': f"{meta['created_at']} · n = {meta['berechnung']['sample_n']}",
                     'report': '/Ergebnisse/Analysen/' + folder.name + '/Bericht/bericht.html',
                     'figures': figures})
    sites = ROOT / '.venv/Lib/site-packages'
    with LOCK:
        return {'appId': APP_ID, 'token': TOKEN, 'job': dict(JOB),
                'datasets': stocks, 'runs': runs,
                'finbert': ((sites / 'torch').is_dir() and (sites / 'transformers').is_dir()
                            and read_json(ROOT / 'Interface/finbert-bereit.json', {}).get('modelltest_bestanden', False))}


def run_job(payload):
    keys = payload.get('keys', {})
    def log(message):
        for secret in keys.values():
            if secret:
                message = message.replace(secret, '[ENTFERNT]')
        with LOCK:
            JOB['messages'] = [*JOB['messages'], message][-200:]
    try:
        env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
        process = subprocess.Popen([str(RUNTIME), '-u', '-B', str(ROOT / 'Interface/auftrag.py')],
                                   cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8', env=env,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        process.stdin.write(json.dumps(payload, ensure_ascii=False))
        process.stdin.close()
        result = None
        for line in process.stdout:
            line = line.rstrip()
            if line.startswith('RESULT '):
                result = json.loads(line[7:])
            elif line:
                log(line)
        code = process.wait()
        with LOCK:
            JOB.update(status='done' if code == 0 else 'failed', result=result,
                       finished_at=datetime.now().astimezone().isoformat())
    except Exception as exc:
        log('Auftrag fehlgeschlagen: ' + str(exc))
        with LOCK:
            JOB.update(status='failed')
    finally:
        keys.clear()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, data, kind='application/json; charset=utf-8'):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def local(self):
        port = self.server.server_port
        return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

    def do_GET(self):
        if not self.local():
            return self.respond(403, {'message': 'Nur lokal erreichbar.'})
        request = unquote(urlsplit(self.path).path)
        if request == '/':
            self.send_response(302)
            self.send_header('Location', '/Interface/index.html')
            self.end_headers()
            return
        if request == '/api/state':
            return self.respond(200, state())
        file = (ROOT / request.lstrip('/')).resolve()
        interface_allowed = request in {
            '/Interface/index.html', '/Interface/interface.js', '/Interface/daten.js',
            '/Interface/steuerung.js', '/Interface/stil.css', '/Interface/steuerung.css',
            '/Interface/README.md'} or request.startswith('/Interface/Abbildungen/')
        allowed = ((interface_allowed and file.is_relative_to(ROOT / 'Interface'))
                   or file.is_relative_to(ROOT / 'Ergebnisse'))
        if not allowed or not file.is_file() or file.suffix.lower() not in {
                '.html', '.js', '.css', '.md', '.png', '.jpg', '.jpeg', '.svg', '.pdf', '.csv', '.json', '.txt'}:
            return self.respond(404, {'message': 'Datei nicht verfügbar.'})
        mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        if file.suffix in {'.md', '.txt', '.csv'}:
            mime = 'text/plain; charset=utf-8'
        return self.respond(200, file.read_bytes(), mime)

    def do_POST(self):
        port = self.server.server_port
        if (not self.local() or self.headers.get('Origin') not in {
                f'http://127.0.0.1:{port}', f'http://localhost:{port}'}
                or not secrets.compare_digest(self.headers.get('X-Event-Token', ''), TOKEN)):
            return self.respond(403, {'message': 'Bitte die lokale Oberfläche neu laden.'})
        try:
            request = urlsplit(self.path).path
            if request == '/api/stop':
                with LOCK:
                    if JOB['status'] == 'running':
                        return self.respond(409, {'message': 'Zuerst den laufenden Auftrag abschließen lassen.'})
                self.respond(200, {'message': 'Interface beendet.'})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if request != '/api/job':
                return self.respond(404, {'message': 'Unbekannter Aufruf.'})
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1000000:
                raise ValueError('Ungültige Anfragegröße.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or payload.get('action') not in ALLOWED:
                raise ValueError('Unbekannter Auftrag.')
            action = payload['action']
            clean = {'action': action}
            if action not in {'reference', 'install'}:
                clean['config'] = config_for(payload)
            if action in {'download', 'resume'}:
                keys = payload.get('keys', {})
                if not isinstance(keys, dict) or set(keys) != {'alpha_vantage', 'serpapi'}:
                    raise ValueError('Schlüssel für Alpha Vantage und SerpAPI eingeben.')
                if any(not isinstance(k, str) or not k.strip() or len(k) > 500 for k in keys.values()):
                    raise ValueError('Beide API-Schlüssel eingeben.')
                clean['keys'] = {key: value.strip() for key, value in keys.items()}
            if action in {'prepare', 'analyse'}:
                status = read_json(DATASETS / clean['config']['bestand'] / 'Nachweise/download_status.json', {})
                if status.get('status') != 'complete':
                    raise ValueError('Die Datensammlung zuerst fortsetzen und abschließen.')
            if action == 'analyse' and not state()['finbert']:
                raise ValueError('Zuerst FinBERT über die Schaltfläche einrichten.')
            if action == 'timings':
                if not isinstance(payload.get('csv'), str):
                    raise ValueError('Eine CSV-Tabelle einfügen.')
                clean['csv'] = payload['csv']
            with LOCK:
                if JOB['status'] == 'running':
                    return self.respond(409, {'message': 'Es läuft bereits ein Auftrag.'})
                JOB.update(status='running', action=action, messages=[], result=None,
                           started_at=datetime.now().astimezone().isoformat(), finished_at=None)
                threading.Thread(target=run_job, args=(clean,), daemon=True).start()
            self.respond(202, {'started': True})
        except (ValueError, TypeError, KeyError, OSError) as exc:
            self.respond(400, {'message': str(exc)[:500]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--no-browser', action='store_true')
    options = parser.parse_args()
    for port in range(options.port, options.port + 20):
        try:
            server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
            break
        except OSError:
            continue
    else:
        raise RuntimeError('Kein freier lokaler Anschluss gefunden.')
    info = {'url': f'http://127.0.0.1:{server.server_port}', 'pid': os.getpid(), 'appId': APP_ID}
    STATUS.write_text(json.dumps(info), encoding='utf-8')
    if not options.no_browser:
        webbrowser.open(info['url'])
    print(info['url'], flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        if read_json(STATUS, {}).get('pid') == os.getpid():
            STATUS.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
