"""Die Ergebnisübersicht nach einem abgeschlossenen Lauf aktualisieren."""
import html, os, json
from Programm.grundlagen.pfade import ORDNER, ERGEBNISSE, REFERENCE, pfad

def aktualisieren():
    target = ORDNER / 'Ergebnisse/Index.html'
    target.parent.mkdir(parents=True, exist_ok=True)

    def link(path):
        return html.escape(os.path.relpath(path, target.parent).replace(os.sep, '/'), quote=True)
    sections = []
    for title, base, pattern in [('Analysen', ERGEBNISSE, 'analyse_*'), ('Kontextvergleiche', ORDNER / 'Ergebnisse/Kontextvergleiche', 'vergleich_*'), ('Transkriptrekonstruktionen', ORDNER / 'Ergebnisse/Transkriptrekonstruktionen', 'lauf_*')]:
        items = []
        for folder in sorted(base.glob(pattern), reverse=True):
            report = pfad(folder, 'bericht.html') if title != 'Transkriptrekonstruktionen' else folder / 'Rekonstruktion.json'
            if not report.exists():
                continue
            proof = pfad(folder, 'Reproduktionspruefung.json')
            manifest = pfad(folder, 'manifest.json')
            config = json.loads(manifest.read_text(encoding='utf-8')).get('config', {}) if manifest.exists() else {}
            art = config.get('return_type')
            status = ' · einfache Renditen' if art == 'simple' else ' · logarithmische Renditen' if art == 'log' else ''
            status += ' · Referenzvergleich bestanden' if proof.exists() and json.loads(proof.read_text(encoding='utf-8')).get('passed') else ''
            items.append('<li><a href="' + link(report) + '">' + html.escape(folder.name) + '</a>' + status + '</li>')
        sections.append('<h2>' + title + '</h2>' + ('<ul>' + ''.join(items) + '</ul>' if items else '<p>Noch kein Lauf vorhanden.</p>'))
    target.write_text('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ergebnisse</title><style>body{font:17px/1.7 system-ui;max-width:1000px;margin:40px auto;padding:0 24px;color:#193e36}a{color:#236a51}</style><p><a href="../README.html">Projektstart</a></p><h1>Ergebnisse</h1><p><a href="' + link(REFERENCE / 'bericht.html') + '">Unveränderter Referenzbericht der Seminararbeit</a></p>' + ''.join(sections) + '</html>', encoding='utf-8')
