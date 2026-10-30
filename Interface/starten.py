"""Vorhandene lokale Oberfläche öffnen oder im Hintergrund starten."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json
import subprocess
import sys
import time
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
INFO = ROOT / 'Interface/server-info.json'
APP_ID = hashlib.sha256(str(ROOT).encode()).hexdigest()[:20]


def laufende_url():
    try:
        info = json.loads(INFO.read_text(encoding='utf-8'))
        if not info['url'].startswith('http://127.0.0.1:'):
            return None
        with urlopen(info['url'] + '/api/state', timeout=1) as response:
            state = json.load(response)
        return info['url'] if state.get('appId') == APP_ID else None
    except (OSError, ValueError, KeyError):
        return None


url = laufende_url()
if not url:
    logfile = (ROOT / 'Interface/server.log').open('a', encoding='utf-8')
    subprocess.Popen([sys.executable, str(ROOT / 'Interface/server.py'), '--no-browser'],
                     cwd=ROOT, stdout=logfile, stderr=logfile,
                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    for _ in range(40):
        time.sleep(0.25)
        url = laufende_url()
        if url:
            break
if url:
    webbrowser.open(url)
else:
    # Fehlerhinweis auch beim Start ohne Konsolenfenster sichtbar machen.
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, 'Die Oberfläche konnte nicht starten. Siehe Interface/server.log.',
                                   'Event Study', 16)
