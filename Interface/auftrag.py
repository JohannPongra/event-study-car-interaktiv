"""Ein einzelner Auftrag; Eingaben inklusive Schlüssel kommen nur über stdin."""
from pathlib import Path
import csv
import io
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def ausfuehren(payload):
    action = payload['action']
    if action == 'reference':
        import analyse
        analyse.main()
        return {'message': 'Referenzanalyse vollständig neu berechnet und geprüft.',
                'run': 'reference', 'report': '/Ergebnisse/Ergebnisse.md'}
    if action == 'install':
        print('FinBERT-Abhängigkeiten in der Umgebung dieser Kopie installieren …', flush=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r',
                        str(ROOT / 'Technik/Abhaengigkeiten/requirements-finbert-lock.txt')],
                       check=True, cwd=ROOT)
        from Programm.sentiment.modell_laden import modell_laden
        from Programm.grundlagen.konfiguration import einstellungen
        from Interface.modell_bereitstellen import bereitstellen
        bereitstellen(ROOT, lambda message: print(message, flush=True))
        tokenizer, model, order, maximum, torch = modell_laden(einstellungen(), print)
        inputs = tokenizer(['Revenue increased.'], return_tensors='pt')
        with torch.inference_mode():
            prediction = model(**inputs).logits
        if prediction.shape != (1, 3) or not torch.isfinite(prediction).all():
            raise ValueError('FinBERT-Probelauf fehlgeschlagen.')
        (ROOT / 'Interface/finbert-bereit.json').write_text(
            json.dumps({'modelltest_bestanden': True}), encoding='utf-8')
        return {'message': 'FinBERT ist eingerichtet. Neue Datenbestände können analysiert werden.'}

    from Programm.grundlagen.konfiguration import einstellungen
    from Programm.grundlagen.pfade import bestand_ordner, pfad
    cfg = einstellungen(payload['config'])
    if action in {'download', 'resume'}:
        from Programm.datenerhebung.sammlung import sammeln
        result = sammeln(cfg, payload['keys'], lambda s: print(s, flush=True))
        return {**result, 'message': 'Datensammlung abgeschlossen. Den Bestand jetzt prüfen und analysieren.'}
    folder = bestand_ordner(cfg)
    if action == 'timings':
        rows = list(csv.DictReader(io.StringIO(payload['csv'])))
        if not rows or len(rows) > 10000:
            raise ValueError('Eine CSV mit event_id, release_timing und source einfügen.')
        seen = set()
        prepared_events = pfad(pfad(folder, 'aufbereitet'), 'events.csv')
        if not prepared_events.exists():
            raise ValueError('Zuerst Daten prüfen, damit die Ereignisse zugeordnet werden können.')
        with prepared_events.open(encoding='utf-8-sig', newline='') as stream:
            known_events = {row['event_id'] for row in csv.DictReader(stream)}
        for row in rows:
            if set(row) != {'event_id', 'release_timing', 'source'}:
                raise ValueError('CSV-Kopf: event_id,release_timing,source')
            if row['event_id'] in seen or row['release_timing'] not in {'AMC', 'BMO'} or not row['source'].strip():
                raise ValueError('Eindeutige Ereignisse, AMC/BMO und eine Quellenangabe sind erforderlich.')
            if row['event_id'] not in known_events:
                raise ValueError('Ereignis gehört nicht zum ausgewählten Bestand: ' + row['event_id'])
            seen.add(row['event_id'])
        file = pfad(pfad(folder, 'roh'), 'veroeffentlichungszeiten.csv')
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['event_id', 'release_timing', 'source'])
            writer.writeheader()
            writer.writerows(rows)
        return {'message': f'{len(rows)} belegte Veröffentlichungszeiten gespeichert. Vorhandene Korrekturtabelle ersetzt.'}

    from Programm.datenaufbereitung.aufbereitung import verarbeiten
    log = lambda s: print(s, flush=True)
    verarbeiten(cfg, log)
    import pandas as pd
    events = pd.read_csv(pfad(pfad(folder, 'aufbereitet'), 'events.csv'))
    missing = events.loc[events.release_timing.eq('unknown'), 'event_id'].tolist()
    print(f'{len(events)} Berichte; {len(missing)} ohne bekannte Veröffentlichungszeit.', flush=True)
    if action == 'prepare':
        return {'message': f'{len(events)} Berichte aufbereitet; {len(missing)} ohne Veröffentlichungszeit.',
                'missing_times': missing}
    if action != 'analyse':
        raise ValueError('Unbekannter Auftrag.')
    if not events.release_timing.eq('AMC').any():
        raise ValueError('Keine als nachbörslich belegten Berichte. Zuerst Veröffentlichungszeiten ergänzen; es werden keine Zeiten geraten.')
    from Programm.sentiment.auswertung import auswerten
    from Programm.berechnung.berechnung import berechnen
    from Programm.statistik.auswertung import regressieren
    auswerten(cfg, log)
    calculated = berechnen(cfg, log)
    result = regressieren(cfg, log)
    return {**result, 'run': result['ordner'],
            'report': '/Ergebnisse/Analysen/' + result['ordner'] + '/Bericht/bericht.html',
            'message': f"Analyse abgeschlossen: {len(calculated['data'])} verwendbare Ereignisse, "
                       f"{len(calculated['exclusions'])} Ausschlüsse."}


if __name__ == '__main__':
    payload = json.load(sys.stdin)
    try:
        result = ausfuehren(payload)
        print('RESULT ' + json.dumps(result, ensure_ascii=False), flush=True)
    except Exception as exc:
        message = str(exc)
        for key in payload.get('keys', {}).values():
            if key:
                message = message.replace(key, '[ENTFERNT]')
        print('FEHLER: ' + message, flush=True)
        sys.exit(1)
    finally:
        payload.get('keys', {}).clear()
