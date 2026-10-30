"""Zentrale Projektpfade und explizite Zuordnung historischer Dateinamen.

Archivpakete werden nie intern umgeschrieben. Neue Bestände und Ausgaben
verwenden die fachlich gegliederte Ablage. pfad() berechnet nur Pfade;
struktur_vorbereiten() legt die Ordner eines neuen Laufs an.
"""
from pathlib import Path
ORDNER = Path(__file__).resolve().parents[2]
ROOT = ORDNER
FROZEN_ID = 'bestand_20261016_100035_d963e3'
BESTAENDE = ORDNER / 'Daten/Arbeitsbestaende'
ERGEBNISSE = ORDNER / 'Ergebnisse/Analysen'
ALTBESTAND = ORDNER / 'Archiv/Referenzbestand' / FROZEN_ID
REFERENCE = ORDNER / 'Archiv/Referenzlauf/analyse_20261022_171939_db9a9f'
EINFACHE_REFERENCE = ORDNER / 'Pruefungen/Testdaten/CAR_einfache_Renditen'
EXPORT = ORDNER / 'Archiv/Transkriptexport_20261015'
BASE = ORDNER / 'Transkripte'
WURZELZUORDNUNG = {'Tests': 'Pruefungen/Protokolle/Temporaer', 'Daten/bestaende/' + FROZEN_ID: 'Archiv/Referenzbestand/' + FROZEN_ID, 'Daten/bestaende': 'Daten/Arbeitsbestaende', 'Daten/Referenz_Seminararbeit': 'Archiv/Referenzlauf', 'Daten/ergebnisse': 'Ergebnisse/Analysen', 'Daten/transkripte_rekonstruiert': 'Ergebnisse/Transkriptrekonstruktionen', 'Daten/letzte_reproduktion.json': 'Ergebnisse/letzte_reproduktion.json', 'Daten/cache/matplotlib': 'Daten/Zwischenspeicher/Matplotlib', 'Daten/cache': 'Daten/Zwischenspeicher', 'EXPORT_LAPTOP_20261015': 'Archiv/Transkriptexport_20261015', 'Modelle': 'Daten/Modelle/FinBERT', 'Interface': 'Programm/oberflaeche', 'einstellungen.json': 'Technik/Konfiguration/einstellungen.json', 'installation.json': 'Technik/Installationsstatus/installation.json', 'installation_fehler.log': 'Technik/Installationsstatus/installation_fehler.log', 'installierte_pakete.txt': 'Technik/Installationsstatus/installierte_pakete.txt', 'METHODIK.md': 'Dokumentation/Methodik/Methodik.md', 'KONTEXT_SENTIMENT.md': 'Dokumentation/Methodik/Kontextsentiment.md', 'PYTHON_KOMPATIBILITAET.md': 'Dokumentation/Einstieg/Python_Kompatibilitaet.md', 'Dokumentation/Dateiinventar_SHA256.json': 'Pruefungen/Dateiinventare/Dateiinventar_SHA256.json', 'Transkripte/README.md': 'Transkripte/Anleitung.md', 'Transkripte/Index.csv': 'Transkripte/Verzeichnisse/Calls.csv', 'Transkripte/Audioverzeichnis_170_Original.csv': 'Transkripte/Verzeichnisse/Audioquellen.csv', 'Transkripte/Entscheidungen.csv': 'Transkripte/Verzeichnisse/Entscheidungen.csv', 'Transkripte/Korrekturen.csv': 'Transkripte/Verzeichnisse/Korrekturen.csv', 'Transkripte/Hoerpruefungen.csv': 'Transkripte/Verzeichnisse/Hoerpruefungen.csv', 'Transkripte/Pruefung.json': 'Pruefungen/Protokolle/Transkripte.json', 'Transkripte/Einzelberichte': 'Transkripte/Berichte'}

def _kategorie(name):
    if name.startswith(('prices', 'volume')):
        return 'Marktdaten'
    if name.startswith(('earnings', 'history')):
        return 'Gewinne'
    if name.startswith(('transcript', 'finbert_saetze')):
        return 'Transkripte'
    if name.startswith(('search', 'trends', 'tone_importiert')):
        return 'Suchinteresse' if not name.startswith('tone') else 'Transkripte'
    return 'Ereignisse'

def _bestand(rest):
    if not rest:
        return rest
    first, *tail = rest
    if first in {'roh', 'Rohdaten'}:
        if not tail:
            return ['Rohdaten']
        if tail[0] in {'Ereignisse', 'Marktdaten', 'Gewinne', 'Suchinteresse', 'Transkripte', 'Importnachweise'}:
            return ['Rohdaten', *tail]
        if tail[0] == 'importbelege':
            return ['Rohdaten', 'Importnachweise', *tail[1:]]
        if tail[0] in {'alpha_vantage', 'serpapi', 'trends'}:
            provider = tail[0]
            category = 'Marktdaten' if provider == 'alpha_vantage' else 'Suchinteresse'
            return ['Rohdaten', category, provider, *tail[1:]]
        return ['Rohdaten', _kategorie(tail[0]), *tail]
    if first in {'aufbereitet', 'Aufbereitet'}:
        if not tail:
            return ['Aufbereitet']
        name = tail[0]
        if name in {'Ereignisse', 'Marktdaten', 'Suchinteresse', 'Transkripte'}:
            return ['Aufbereitet', *tail]
        if name == 'kontext':
            return ['Sentiment', 'Kontext', *tail[1:]]
        if name in {'tone.csv', 'finbert.json'}:
            return ['Sentiment', 'Tonalitaet', *tail]
        if name == 'finbert_saetze.csv':
            return ['Sentiment', 'Satzvorhersagen', *tail]
        if name == 'verarbeitung.json':
            return ['Nachweise', *tail]
        category = _kategorie(name)
        if category == 'Gewinne':
            category = 'Ereignisse'
        return ['Aufbereitet', category, *tail]
    if first in {'berechnet', 'Berechnet'}:
        if not tail:
            return ['Berechnet']
        name = tail[0]
        if name in {'Ereignisrenditen', 'Einflussgroessen', 'Analysestichprobe', 'Exporte'}:
            return ['Berechnet', *tail]
        if name == 'berechnung.json':
            return ['Nachweise', *tail]
        if name.startswith(('event_study', 'PSPP', 'Variablenverzeichnis', 'Jamovi', 'Uebersichtliche_Daten')):
            return ['Berechnet', 'Exporte', *tail]
        category = 'Ereignisrenditen' if name == 'daily.csv' else 'Einflussgroessen' if name == 'history.csv' else 'Analysestichprobe'
        return ['Berechnet', category, *tail]
    if first in {'finbert_cache.csv', 'finbert_lc_cache.csv'}:
        return ['Sentiment', 'Satzvorhersagen', *rest]
    if first.endswith('.json') and first != 'bestand.json':
        return ['Nachweise', *rest]
    return rest

def _analyse(rest):
    if not rest:
        return rest
    name, *tail = rest
    if name in {'Bericht', 'Tabellen', 'Grafiken', 'Modelle', 'Exporte', 'Nachweise'} or name == 'manifest.json':
        return rest
    if name == 'bericht.html':
        return ['Bericht', *rest]
    if name == 'skripte':
        return ['Nachweise', 'Programmstand', *tail]
    if name.startswith(('Jamovi', 'Uebersichtliche_Daten')):
        return ['Exporte', 'Jamovi', *rest]
    if name.startswith('PSPP') or name == 'Variablenverzeichnis.csv':
        return ['Exporte', 'PSPP', *rest]
    if name.startswith('event_study.') and name.endswith('sqlite'):
        return ['Exporte', 'SQLite', *rest]
    if name.endswith(('.png', '.pdf')):
        return ['Grafiken', *rest]
    if '.' not in name and (name.startswith(('car_', 'abs_car_')) or name == 'ueberblick'):
        return ['Grafiken', *rest]
    if name.endswith('_modell.txt'):
        return ['Modelle', *rest]
    if name.endswith('.csv'):
        group = 'Robustheit' if name.startswith(('ABS_CAR', 'robustheit', 'unternehmensauswahl')) else 'Diagnostik' if name.startswith(('diagnostik', 'residuen', 'vif', 'korrelationen')) else 'Hauptmodelle' if name in {'koeffizienten.csv', 'event_study.csv'} else 'Stichprobe'
        return ['Tabellen', group, *rest]
    return ['Nachweise', *rest]

def pfad(basis, *teile):
    """Projektpfad aus Bestand/Lauf und einem fachlichen Dateinamen bilden."""
    result = Path(basis).joinpath(*teile)
    try:
        rel = result.relative_to(ORDNER).as_posix()
    except ValueError:
        return result
    for old, new in sorted(WURZELZUORDNUNG.items(), key=lambda x: len(x[0]), reverse=True):
        if rel == old or rel.startswith(old + '/'):
            rel = new + rel[len(old):]
            break
    parts = rel.split('/')
    if parts[:2] == ['Daten', 'Arbeitsbestaende'] and len(parts) >= 3:
        if parts[2] == FROZEN_ID:
            return ALTBESTAND.joinpath(*parts[3:])
        parts = parts[:3] + _bestand(parts[3:])
        if len(parts) > 6 and parts[3:6] == ['Rohdaten', 'Marktdaten', 'alpha_vantage']:
            if parts[6].startswith('earnings_'):
                parts[4] = 'Gewinne'
            elif parts[6].startswith('transcript_'):
                parts[4] = 'Transkripte'
    elif parts[:2] == ['Ergebnisse', 'Analysen'] and len(parts) >= 3:
        if parts[2].startswith('vergleich_'):
            parts[1] = 'Kontextvergleiche'
        else:
            parts = parts[:3] + _analyse(parts[3:])
    elif parts[:3] == ['Daten', 'Modelle', 'FinBERT'] and len(parts) > 3:
        parts[3] = parts[3].removeprefix('finbert-tone-')
    elif len(parts) == 3 and parts[0] == 'Transkripte' and (parts[1] in {'Audio', 'Berichte'}) and ('_' in parts[2]):
        event = parts[2].split('.')[0]
        ticker, day = event.split('_', 1)
        parts = parts[:2] + [ticker, day[:4], parts[2]]
    if len(parts) == 2 and parts[0] == 'requirements-Versionen.json':
        parts = ['Technik', 'Abhaengigkeiten', *parts]
    if rel.startswith('requirements'):
        parts = ['Technik', 'Abhaengigkeiten', *rel.split('/')]
    return ORDNER.joinpath(*parts)

def dateien(basis, muster='*'):
    """Dateien eines fachlichen Bereichs finden, auch nach dessen Untergliederung."""
    basis = Path(basis)
    if basis.parent == ERGEBNISSE:
        return basis.rglob(muster)
    try:
        rel = basis.relative_to(BESTAENDE)
    except ValueError:
        return basis.glob(muster)
    if len(rel.parts) >= 2:
        stage = rel.parts[1]
        if stage in {'Rohdaten', 'Aufbereitet', 'Berechnet'}:
            if basis.name == 'alpha_vantage' and muster.startswith(('earnings_', 'transcript_')):
                category = 'Gewinne' if muster.startswith('earnings_') else 'Transkripte'
                return (BESTAENDE / rel.parts[0] / 'Rohdaten' / category / 'alpha_vantage').glob(muster)
            found = list(basis.rglob(muster))
            if stage == 'Aufbereitet' and len(rel.parts) == 2:
                dataset = BESTAENDE / rel.parts[0]
                found += list((dataset / 'Sentiment').rglob(muster))
            return sorted(set(found))
    return basis.glob(muster)

def bestand_ordner(cfg):
    if not cfg['bestand']:
        raise ValueError('Zuerst Daten importieren oder einen neuen Datenbestand herunterladen.')
    folder = pfad(BESTAENDE, cfg['bestand'])
    if not folder.is_dir():
        raise ValueError('Datenbestand ist nicht vorhanden.')
    return folder

def struktur_vorbereiten(folder):
    """Verzeichnisse eines neuen Bestands oder Ergebnislaufs initialisieren."""
    folder = Path(folder)
    if folder.parent == BESTAENDE:
        paths = ['Rohdaten/' + x for x in ['Ereignisse', 'Marktdaten/alpha_vantage', 'Gewinne', 'Suchinteresse/serpapi', 'Suchinteresse/trends', 'Transkripte', 'Importnachweise']]
        paths += ['Aufbereitet/' + x for x in ['Ereignisse', 'Marktdaten', 'Suchinteresse', 'Transkripte']]
        paths += ['Sentiment/' + x for x in ['Satzvorhersagen', 'Tonalitaet', 'Kontext']]
        paths += ['Berechnet/' + x for x in ['Ereignisrenditen', 'Einflussgroessen', 'Analysestichprobe', 'Exporte']] + ['Nachweise']
    elif folder.parent == ERGEBNISSE:
        paths = ['Bericht', 'Grafiken', 'Modelle', 'Exporte/Jamovi', 'Exporte/PSPP', 'Exporte/SQLite', 'Nachweise'] + ['Tabellen/' + x for x in ['Stichprobe', 'Hauptmodelle', 'Diagnostik', 'Robustheit']]
    else:
        return
    for p in paths:
        (folder / p).mkdir(parents=True, exist_ok=True)

def rohbestand_gliedern(folder):
    """Kopierte eingefrorene Rohdaten einmalig in die neue Arbeitsablage übernehmen."""
    struktur_vorbereiten(folder)
    raw = pfad(folder, 'roh')
    for p in list(raw.rglob('*')):
        if not p.is_file():
            continue
        relative = p.relative_to(raw)
        if relative.parts[0] in {'Ereignisse', 'Marktdaten', 'Gewinne', 'Suchinteresse', 'Transkripte', 'Importnachweise'}:
            continue
        target = pfad(raw, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        p.rename(target)
    for p in sorted(raw.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if p.is_dir() and (not any(p.iterdir())):
            p.rmdir()

def schreibziel_pruefen(path):
    """Unbeabsichtigte Änderungen historischer Originalpakete verhindern."""
    path = Path(path).resolve()
    archiv = (ORDNER / 'Archiv').resolve()
    if path == archiv or archiv in path.parents:
        raise ValueError('Die eingefrorenen Originaldaten im Archiv sind schreibgeschützt. REPRODUZIEREN.bat legt einen getrennten Arbeitsbestand an; für eigene Daten zuerst einen neuen Bestand importieren.')
    return path
