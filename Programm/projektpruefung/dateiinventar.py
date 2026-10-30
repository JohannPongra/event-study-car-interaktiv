"""Identität des neuen Projektstands prüfen; historische Inventare bleiben erhalten."""
from Programm.grundlagen.pfade import pfad
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, sys
from Programm.grundlagen.pfade import ORDNER as ROOT
MANIFEST = pfad(ROOT, 'Pruefungen/Dateiinventare/Dateiinventar_SHA256.json')
PAYLOAD = ['Archiv', 'Daten/Modelle', 'Transkripte', 'Programm', 'Dokumentation', 'Technik/Abhaengigkeiten', 'Technik/Konfiguration', 'Technik/Startdateien', 'Pruefungen/Tests', 'Pruefungen/Testdaten']

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def candidates():
    files = set()
    for name in PAYLOAD:
        files.update((p for p in (ROOT / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.suffix not in {'.pyc', '.pyo'})))
    files.update(ROOT.glob('*.bat'))
    files.update(ROOT.glob('README.*'))
    files.add(pfad(ROOT, '.gitignore'))
    return sorted(files)

def inventar():
    data = {p.relative_to(ROOT).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in candidates()}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({'schema': 2, 'scope': 'Archiv, Eingaben, Audios, Modelle, Programm, Dokumentation und Tests. Lauf- und Installationsausgaben bleiben veränderlich.', 'files': data}, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'files': len(data), 'bytes': sum((x['bytes'] for x in data.values()))}

def pruefen(mit_grossen_dateien=False):
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    checked = 0
    large = 0
    expected = set(data['files'])
    actual = {p.relative_to(ROOT).as_posix() for p in candidates()}
    if expected != actual:
        raise ValueError('Eingaben fehlen oder wurden ergänzt: ' + repr(sorted(expected ^ actual)[:8]))
    for name, v in data['files'].items():
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or ':' in name or ('\\' in name):
            raise ValueError('Ungültiger Inventarpfad')
        p = ROOT / name
        if not p.is_file() or p.stat().st_size != v['bytes']:
            raise ValueError('Datei fehlt oder Größe verändert: ' + name)
        if v['bytes'] > 20000000 and (not mit_grossen_dateien):
            large += 1
            continue
        if sha(p) != v['sha256']:
            raise ValueError('Datei verändert: ' + name)
        checked += 1
    return {'sha256_checked': checked, 'large_files_size_only': large, 'full_hash_check': mit_grossen_dateien}

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventar-erstellen', action='store_true')
    p.add_argument('--vollstaendig', action='store_true')
    a = p.parse_args(argv)
    try:
        print(json.dumps(inventar() if a.inventar_erstellen else pruefen(a.vollstaendig), ensure_ascii=False))
    except (ValueError, OSError) as e:
        print('Prüfung fehlgeschlagen: ' + str(e), file=sys.stderr)
        return 1
    return 0
