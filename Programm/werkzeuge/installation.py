"""werkzeuge · installation – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
import argparse
from datetime import datetime
import json
import struct
import subprocess
import sys
import venv
from Programm.grundlagen.pfade import ORDNER
MINIMUM = (3, 12)

def python_pruefen(version=None, bits=None):
    version = sys.version_info if version is None else version
    bits = struct.calcsize('P') * 8 if bits is None else bits
    if tuple(version[:2]) != (3, 12):
        raise ValueError('Für diese Reproduktion bitte Python 3.12 in 64 Bit verwenden. Getestet: 3.12.14.')
    if bits != 64:
        raise ValueError('Bitte die 64-Bit-Ausgabe von Python verwenden.')

def python_datei(umgebung):
    return pfad(umgebung, 'Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')

def umgebung_vorbereiten(wechsel=False):
    umgebung = pfad(ORDNER, '.venv')
    python = python_datei(umgebung)
    if umgebung.exists():
        try:
            result = subprocess.run([str(python), '-c', 'import sys,json; print(json.dumps(list(sys.version_info[:2])))'], check=True, capture_output=True, text=True)
            vorhanden = tuple(json.loads(result.stdout))
        except (OSError, subprocess.CalledProcessError, ValueError):
            vorhanden = None
        if vorhanden == tuple(sys.version_info[:2]):
            return python
        if not wechsel:
            raise ValueError('Die vorhandene .venv ist defekt oder nutzt eine andere Python-Version. INSTALLIEREN.bat mit der gewünschten Version starten, z. B. INSTALLIEREN.bat 3.14.')
        sicherung = pfad(ORDNER, '.venv-sicherung-' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        if umgebung.is_symlink() or umgebung.resolve().parent != ORDNER or sicherung.resolve().parent != ORDNER:
            raise ValueError('Die Python-Umgebung liegt außerhalb dieses Projektordners. Wechsel abgebrochen.')
        umgebung.rename(sicherung)
        print('Bisherige Python-Umgebung gesichert als ' + sicherung.name, flush=True)
    print('Erstelle Python-Umgebung mit ' + sys.version.split()[0], flush=True)
    venv.EnvBuilder(with_pip=True).create(umgebung)
    return python

def ausfuehren(python, *argumente):
    subprocess.run([str(python), *argumente], cwd=ORDNER, check=True)

def importe_pruefen(python, module):
    result = subprocess.run([str(python), '-c', module], cwd=ORDNER, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        log = pfad(ORDNER, 'installation_fehler.log')
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        if 'Anwendungssteuerungsrichtlinie' in result.stderr or 'application control' in result.stderr.lower() or 'WinError 4551' in result.stderr:
            raise ValueError('Windows-Anwendungssteuerung blockiert eine Paketdatei. Details stehen in installation_fehler.log. Die Sperre muss durch die zuständige Windows-Verwaltung geprüft werden.')
        raise ValueError('Ein Paket lässt sich nicht laden. Details stehen in installation_fehler.log.')

def installieren(finbert=False, wechsel=False):
    python_pruefen()
    python = umgebung_vorbereiten(wechsel)
    pakete = ['-r', str(pfad(ORDNER, 'requirements.txt'))]
    if finbert:
        pakete.extend(['-r', str(pfad(ORDNER, 'requirements-finbert.txt'))])
    ausfuehren(python, '-m', 'pip', 'install', '--only-binary=:all:', *pakete)
    ausfuehren(python, '-m', 'pip', 'check')
    module = 'import Programm.datenerhebung.sammlung, Programm.datenaufbereitung.aufbereitung, Programm.sentiment.auswertung, Programm.berechnung.berechnung, Programm.statistik.auswertung, Programm.oberflaeche.server'
    if finbert:
        module += '; import torch; from transformers import AutoTokenizer,AutoModelForSequenceClassification'
    importe_pruefen(python, module)
    lock = subprocess.run([str(python), '-m', 'pip', 'freeze'], check=True, capture_output=True, text=True).stdout
    status_code = "import json,platform,sys; print(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'executable':sys.executable}))"
    status = json.loads(subprocess.run([str(python), '-c', status_code], check=True, capture_output=True, text=True).stdout)
    status.update({'erstellt': datetime.now().astimezone().isoformat(), 'finbert_geprueft': finbert, 'pruefung': 'Paketabhängigkeiten und Modulimporte; keine vollständige Analyse'})
    pfad(ORDNER, 'installierte_pakete.txt').write_text(lock, encoding='utf-8')
    pfad(ORDNER, 'installation.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Installation geprüft: Python ' + status['python'] + '. REPRODUZIEREN.bat öffnen.', flush=True)

def main():
    parser = argparse.ArgumentParser(description='Event Study für das ausführende Python installieren')
    parser.add_argument('python_version', nargs='?', choices=['3.12'], help='Festgelegte Python-Version')
    parser.add_argument('--finbert', action='store_true', help='Zusätzlich neue Textbewertungen ermöglichen')
    parser.add_argument('--wechsel', action='store_true', help='Abweichende/defekte .venv sichern und neu anlegen')
    args = parser.parse_args()
    try:
        installieren(args.finbert, args.wechsel)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print('\nInstallation nicht abgeschlossen: ' + str(exc), file=sys.stderr)
        print('Meldung oben beachten. Internetzugang und verfügbare Pakete für diese Python-Version prüfen. Für sehr neue Versionen können fertige Pakete noch fehlen. Getestete Alternative: INSTALLIEREN.bat 3.12. Vor einem Versionswechsel die Oberfläche schließen.', file=sys.stderr)
        return 1
    return 0
