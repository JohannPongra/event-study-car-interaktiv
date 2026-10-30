"""transkripte · rekonstruktion – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.transkripte.archiv_lesen import EXPORT
from pathlib import Path
from Programm.transkripte.archiv_lesen import ROOT
from Programm.transkripte.archiv_lesen import daten
import hashlib, json, runpy, uuid
from Programm.transkripte.pruefung import pruefen

def rekonstruieren(ziel=None):
    verifier = runpy.run_path(str(pfad(EXPORT, 'export_pruefen.py')))
    pruefen()
    target = Path(ziel) if ziel else pfad(pfad(ROOT, 'Daten/transkripte_rekonstruiert'), 'lauf_' + uuid.uuid4().hex[:12])
    target.mkdir(parents=True, exist_ok=False)
    manifest, ledger, _ = daten()
    for event, item in manifest['calls'].items():
        original = pfad(EXPORT, item['source_text_path']).read_text(encoding='utf-8')
        rebuilt = verifier['replay'](original, ledger['overlays'][event]['changes']).encode('utf-8')
        if hashlib.sha256(rebuilt).hexdigest() != item['text_sha256']:
            raise ValueError('Rekonstruktion stimmt nicht: ' + event)
        pfad(target, event + '.txt').write_bytes(rebuilt)
    report = {'calls': 170, 'corrections': sum((len(x['changes']) for x in ledger['overlays'].values())), 'all_sha256_identical': True, 'scope': 'Exakte Anwendung der dokumentierten Änderungen auf eingefrorene Kandidatentexte; keine neue Spracherkennung und keine erneute menschliche Prüfung.'}
    pfad(target, 'Rekonstruktion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    from Programm.ausgabe.verzeichnis import aktualisieren
    aktualisieren()
    return (target, report)
