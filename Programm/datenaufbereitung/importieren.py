"""datenaufbereitung · importieren – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad, dateien
from Programm.grundlagen.pfade import ALTBESTAND
from Programm.grundlagen.pfade import BESTAENDE
from Programm.grundlagen.pfade import ORDNER
from pathlib import Path
from Programm.grundlagen.konfiguration import einstellungen
from Programm.grundlagen.laufkennungen import kennung
from Programm.grundlagen.pruefsummen import pruefsumme
import shutil
from Programm.grundlagen.json_dateien import speichern
from Programm.grundlagen.laufkennungen import zeit

def importieren(quelle=ALTBESTAND, werte=None, fortschritt=print):
    """Kopieren, niemals die ursprünglichen Daten verändern oder verknüpfen."""
    source = Path(quelle).expanduser().resolve()
    if pfad(pfad(source, '03_daten'), 'aktueller_stand').is_dir():
        source = pfad(pfad(source, '03_daten'), 'aktueller_stand')
    if not source.is_dir() or BESTAENDE.resolve() == source or BESTAENDE.resolve() in source.parents:
        raise ValueError('Einen externen Datenordner oder den bisherigen Upload-Ordner angeben.')
    cfg = einstellungen(werte)
    cfg['bestand'] = kennung('bestand')
    folder = pfad(BESTAENDE, cfg['bestand'])
    raw = pfad(folder, 'roh')
    raw.mkdir(parents=True)
    files = []

    def kopie(src, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        files.append({'quelle': str(src), 'datei': str(dest.relative_to(folder)), 'sha256': pruefsumme(dest)})
    old = pfad(source, 'aufbereitet')
    mapping = {'events.csv': 'events.csv', 'prices.csv': 'prices.csv', 'volume.csv': 'volume.csv', 'transcript_turns.csv': 'transcripts.csv', 'tone.csv': 'tone_importiert.csv', 'search.csv': 'search_importiert.csv'}
    for original, target in mapping.items():
        path = old / original if (old / original).is_file() else pfad(source, target)
        if path.is_file():
            kopie(path, pfad(raw, target))
    for name in ['earnings_history.csv', 'veroeffentlichungszeiten.csv', 'transcripts.csv', 'tone_importiert.csv', 'search_importiert.csv']:
        if pfad(source, name).is_file() and (not pfad(raw, name).exists()):
            kopie(pfad(source, name), pfad(raw, name))
    for path in sorted(dateien(pfad(pfad(source, 'roh'), 'earnings'), '*_earnings_raw.json')):
        kopie(path, pfad(pfad(raw, 'alpha_vantage'), 'earnings_' + path.name.split('_')[0] + '.json'))
    for sub in [pfad(pfad(source, 'roh'), 'google_trends'), pfad(pfad(source, 'nachweise'), 'sources'), pfad(source, 'trends')]:
        for path in sorted(sub.glob('*.csv')):
            if 'Trends' in path.name or sub.name in {'google_trends', 'trends'}:
                kopie(path, pfad(pfad(raw, 'trends'), path.name))
    for provider in ['alpha_vantage', 'serpapi']:
        sub = pfad(pfad(source, 'roh'), provider)
        for path in sorted(sub.glob('*.json')):
            if not pfad(pfad(raw, provider), path.name).exists():
                kopie(path, pfad(pfad(raw, provider), path.name))
    for relative in ['nachweise', 'aufbereitung_nachweise', 'roh/marktdaten', 'roh/earnings_transcripts']:
        sub = pfad(source, relative)
        for path in sorted(sub.rglob('*')):
            if path.is_file():
                kopie(path, pfad(pfad(pfad(raw, 'importbelege'), relative), path.relative_to(sub)))
    if not pfad(raw, 'prices.csv').exists() and (not list(dateien(pfad(raw, 'alpha_vantage'), 'prices_*.json'))):
        raise ValueError('Keine Kursdaten gefunden. Importvorlagen und Anleitung beachten. Der angelegte Bestand ist unvollständig.')
    speichern(pfad(folder, 'bestand.json'), {'art': 'import', 'quelle': str(source), 'created_at': zeit(), 'config': cfg, 'dateien': files})
    speichern(pfad(ORDNER, 'einstellungen.json'), cfg)
    fortschritt(f"{len(files)} Dateien kopiert. Bestand: {cfg['bestand']}")
    return {'bestand': cfg['bestand'], 'dateien': len(files)}
