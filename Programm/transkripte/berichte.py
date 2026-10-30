"""transkripte · berichte – klar abgegrenzter Projektbaustein."""
from Programm.transkripte.zuordnung import call_datei
from Programm.grundlagen.pfade import pfad
from Programm.transkripte.archiv_lesen import BASE
from Programm.transkripte.archiv_lesen import FROZEN
from Programm.transkripte.archiv_lesen import ROOT
import argparse, html, json
from Programm.transkripte.archiv_lesen import daten
from collections import defaultdict
from Programm.transkripte.pruefung import pruefen
from Programm.transkripte.rekonstruktion import rekonstruieren
from Programm.transkripte.archiv_lesen import rows
from Programm.transkripte.verzeichnisse import writecsv
from Programm.transkripte.audio import zeitbereich
CSS = 'body{font:16px/1.5 system-ui,sans-serif;margin:32px auto;max-width:1180px;padding:0 22px;color:#17202a}a{color:#17588b}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;vertical-align:top;border:1px solid #d7dde2;padding:8px}th{background:#edf1f4}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.5 Georgia,serif}input{font:inherit;padding:10px;width:min(95%,600px);margin:12px 0}summary{cursor:pointer;font-weight:600;padding:10px 0}audio{width:min(100%,650px)}.meta{color:#42515e}code{overflow-wrap:anywhere}h1,h2{line-height:1.2}ins{background:#e2f1e5;text-decoration:none}del{background:#f8e4e4}'

def page(title, body):
    return '<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>' + html.escape(title) + '</title><style>' + CSS + '</style><body>' + body + '</body></html>'

def esc(t):
    return html.escape(str(t))

def bericht():
    status = pruefen()
    manifest, ledger, human = daten()
    BASE.mkdir(exist_ok=True)
    details = pfad(BASE, 'Einzelberichte')
    details.mkdir(exist_ok=True)
    audio = {r['event_id']: r for r in rows(pfad(BASE, 'Audioverzeichnis_170_Original.csv'), ';')}
    tones = {r['event_id']: r for r in rows(pfad(FROZEN, 'aufbereitet/tone.csv'))}
    decisions = defaultdict(list)
    reviews = defaultdict(list)
    for d in ledger['decisions']:
        decisions[d['event_id']].append(d)
    for h in human:
        reviews[h['Call']].append(h)
    corrections = []
    index = []
    flatdecisions = []
    flathear = []
    for event, item in sorted(manifest['calls'].items()):
        a = audio[event]
        overlay = ledger['overlays'][event]
        tone = tones[event]
        textpath = call_datei('Texte', event, '.txt').relative_to(ROOT).as_posix()
        candidate = 'EXPORT_LAPTOP_20261015/' + item['source_text_path']
        entry = {'event_id': event, 'ticker': a['ticker'], 'reported_date': a['reported_date'], 'quellseite': a['page_url'], 'audio_url': a['audio_url'], 'audio_datei': 'Transkripte/Audio/' + event + '.mpeg', 'audio_sha256': a['sha256'], 'dauer_sekunden': a['duration_seconds'], 'endtext': textpath, 'endtext_sha256': item['text_sha256'], 'kandidat': candidate, 'kandidat_sha256': overlay['source_text_sha256'], 'entscheidungen': len(decisions[event]), 'hoerpruefungen': len(reviews[event]), 'textkorrekturen': len(overlay['changes']), 'n_positive': tone['n_positive'], 'n_negative': tone['n_negative'], 'n_neutral': tone['n_neutral'], 'tone': tone['tone'], 'satzbewertungen': 'Daten/bestaende/bestand_20261016_100035_d963e3/aufbereitet/finbert_saetze.csv', 'einzelbericht': 'Transkripte/Einzelberichte/' + event + '.html'}
        index.append(entry)
        changetable = ''
        for c in overlay['changes']:
            corrections.append({'event_id': event, 'start_char': c['start_char'], 'end_char': c['end_char'], 'original': c['original'], 'replacement': c['replacement'], 'episode_id': c.get('episode_id', ''), 'kandidat_sha256': overlay['source_text_sha256'], 'endtext_sha256': item['text_sha256'], 'vollbeleg': 'EXPORT_LAPTOP_20261015/Nachweise/Entscheidungen.json'})
            changetable += '<tr><td>' + str(c['start_char']) + '–' + str(c['end_char']) + '</td><td>' + esc(c['original']) + '</td><td>' + esc(c['replacement'] or '[entfernt]') + '</td><td>' + esc(c.get('episode_id', '')) + '</td></tr>'
        heartable = ''
        for h in reviews[event]:
            start, end = zeitbereich(h['Zeit'])
            link = '../Audio/' + event + '.mpeg#t=' + str(max(0, start - 10)) + ',' + str(end + 10)
            flathear.append({'event_id': event, 'issue_id': h['ID'], 'beginn_sekunden': start, 'ende_sekunden': end, 'sekundenquelle': 'Originalfeld Zeit (mm:ss.mmm)', 'beginn_feld_original': h['Beginn_Sekunden'], 'ende_feld_original': h['Ende_Sekunden'], 'pruefgrund': h['Pruefgrund'], 'hoerentscheidung_original': h['Hoerentscheidung'], 'notiz_original': h['Notiz'], 'audio_datei': entry['audio_datei'], 'audio_startlink': entry['audio_datei'] + '#t=' + str(max(0, start - 10)) + ',' + str(end + 10)})
            heartable += '<tr><td><a href="' + esc(link) + '">' + esc(h['Zeit']) + '</a></td><td>' + esc(h['Pruefgrund']) + '</td><td>' + esc(h['Hoerentscheidung']) + '</td></tr>'
        for d in decisions[event]:
            flatdecisions.append({'event_id': event, 'issue_id': d['issue_id'], 'art': d['kind'], 'status': d['status'], 'methode': d['method'], 'automatisch': d.get('automatic', ''), 'menschliche_hoerpruefung': d.get('human_audio_review_asserted', False), 'vollbeleg': 'EXPORT_LAPTOP_20261015/Nachweise/Entscheidungen.json'})
        body = '<p><a href="../Index.html">Alle 170 Calls</a> · <a href="../../README.html">Projektstart</a></p><h1>' + esc(event) + '</h1>'
        body += '<p><a href="' + esc(a['page_url']) + '">Ursprüngliche Stock-Analysis-Seite</a> · Anbieter: Quartr · Audio ' + str(round(float(a['duration_seconds']) / 60, 1)) + ' Minuten</p>'
        body += '<audio controls preload="none" src="../Audio/' + event + '.mpeg"></audio>'
        body += '<p><a href="../../' + textpath + '">Endtext öffnen</a> · <a href="../../' + candidate + '">Eingefrorenen Kandidatentext öffnen</a></p>'
        body += '<p class="meta">Die Kandidaten sind bereits aufbereitete Prüftexte. Sie sind keine unveränderten Rohtranskripte von Whisper. Zeichenpositionen der Änderungen beziehen sich auf diesen Kandidaten.</p>'
        body += '<h2>Verbindung zur Analyse</h2><p>Positive Sätze: ' + esc(tone['n_positive']) + ' · negative: ' + esc(tone['n_negative']) + ' · neutrale: ' + esc(tone['n_neutral']) + '. TONE = ' + esc(tone['tone']) + '. Alle Sprecher des gesamten Calls sind enthalten; keine Sprecherzuordnung wurde erfunden.</p>'
        body += '<p>Identität des Endtexts: <code>' + item['text_sha256'] + '</code>. Der importierte und der aufbereitete Analysetext sind zeichengetreu identisch mit dieser Endfassung.</p>'
        body += '<h2>Gezielte menschliche Hörprüfungen</h2>'
        body += '<table><tr><th>Zeit im Audio</th><th>Prüfgrund</th><th>Originalentscheidung</th></tr>' + heartable + '</table>' if heartable else '<p>Für diesen Call ist keine der 57 gezielten menschlichen Hörprüfungen verzeichnet.</p>'
        body += '<p>Die Hörprüfungen decken gezielt markierte Stellen ab. Der ganze Call wurde dadurch nicht vollständig menschlich abgehört. Je nach Browser öffnet der Audiolink die bezeichnete Stelle oder die gesamte Aufnahme.</p>'
        body += '<h2>Dokumentierte Textänderungen</h2>'
        body += '<table><tr><th>Zeichenbereich im Kandidaten</th><th>Vorher</th><th>Nachher</th><th>Belegkennung</th></tr>' + changetable + '</table>' if changetable else '<p>Zwischen dem eingefrorenen Kandidaten und dem Endtext liegt keine Änderung vor.</p>'
        body += '<p>Alle ' + str(len(decisions[event])) + ' historischen Prüfentscheidungen stehen in <a href="../Entscheidungen.csv">Entscheidungen.csv</a>; vollständige verschachtelte Belege in <a href="../../EXPORT_LAPTOP_20261015/Nachweise/Entscheidungen.json">Entscheidungen.json</a>. Historische Pfade darin bleiben Herkunftsangaben.</p>'
        body += '<details><summary>Vollständigen Endtext lesen</summary><pre>' + esc(pfad(ROOT, textpath).read_text(encoding='utf-8')) + '</pre></details>'
        seite_speichern(event, page(event, body))
    for filename, data in [('Index.csv', index), ('Korrekturen.csv', corrections), ('Entscheidungen.csv', flatdecisions), ('Hoerpruefungen.csv', flathear)]:
        writecsv(pfad(BASE, filename), data, list(data[0]))
    table = ''.join(('<tr><td><a href="Einzelberichte/' + r['event_id'] + '.html">' + r['event_id'] + '</a></td><td>' + str(r['hoerpruefungen']) + '</td><td>' + str(r['textkorrekturen']) + '</td><td>' + str(r['tone']) + '</td><td><a href="../' + r['endtext'] + '">TXT</a></td></tr>' for r in index))
    body = '<p><a href="../README.html">Projektstart</a></p><h1>Herkunft und Bearbeitung der 170 Transkripte</h1><p>Ein Call verbindet Originalaudio → dokumentierte Prüftexte und Korrekturen → Endtext → Satzbewertungen → TONE.</p>'
    body += '<p>Enthalten: 170 Originalaudios, 170 Endtexte, 429 dokumentierte Prüfentscheidungen, 129 Textänderungen gegenüber den eingefrorenen Kandidaten und 57 gezielte menschliche Hörprüfungen. Diese Zahlen beziehen sich auf unterschiedliche Ebenen und werden nicht gleichgesetzt.</p>'
    body += '<p><a href="Index.csv">Index als CSV</a> · <a href="Hoerpruefungen.csv">57 Hörprüfungen</a> · <a href="Korrekturen.csv">129 Änderungen</a> · <a href="Entscheidungen.csv">429 Prüfentscheidungen</a> · <a href="README.md">Ablauf und Grenzen</a></p>'
    body += '<label>Call suchen<br><input id="suche" placeholder="Zum Beispiel AAPL oder 2024-05-02"></label><table><thead><tr><th>Call und Einzelnachweis</th><th>Hörprüfstellen</th><th>Änderungen</th><th>TONE</th><th>Endtext</th></tr></thead><tbody id="calls">' + table + '</tbody></table>'
    body += '<script>document.getElementById("suche").addEventListener("input",function(){const q=this.value.toLowerCase();document.querySelectorAll("#calls tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script>'
    index_speichern(page('170 Transkripte nachvollziehen', body))
    pfad(BASE, 'Pruefung.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    return status

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pruefen', action='store_true')
    p.add_argument('--mit-audio', action='store_true')
    p.add_argument('--rekonstruieren', action='store_true')
    p.add_argument('--bericht', action='store_true')
    p.add_argument('--oeffnen', action='store_true')
    a = p.parse_args()
    if a.oeffnen:
        import webbrowser
        webbrowser.open((BASE / 'Index.html').as_uri())
    elif a.rekonstruieren:
        target, result = rekonstruieren()
        print(target)
        print(json.dumps(result, ensure_ascii=False))
    elif a.bericht:
        print(json.dumps(bericht(), ensure_ascii=False))
    else:
        print(json.dumps(pruefen(a.mit_audio), ensure_ascii=False))

def seite_speichern(event, text):
    from Programm.ausgabe.bericht.verweise import verweise
    target = call_datei('Berichte', event, '.html')
    target.parent.mkdir(parents=True, exist_ok=True)
    old = ROOT / 'Transkripte/Einzelberichte' / (event + '.html')
    proof = call_datei('Nachweise', event, '.json')
    import os
    proof_link = '<p><a href="' + os.path.relpath(proof, target.parent).replace(os.sep, '/') + '">Nachweise zu diesem Call</a></p>'
    text = verweise(text, old, target)
    target.write_text(text.replace('</body>', proof_link + '</body>'), encoding='utf-8')

def index_speichern(text):
    from Programm.ausgabe.bericht.verweise import verweise
    target = BASE / 'Index.html'
    target.write_text(verweise(text, target, target), encoding='utf-8')
