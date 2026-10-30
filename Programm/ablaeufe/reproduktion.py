"""ablaeufe · reproduktion – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import ROOT
from Programm.grundlagen.pfade import pfad
import argparse, json, shutil, sys
from Programm.projektpruefung.offlinebetrieb import ohne_netzwerk
from Programm.projektpruefung.referenzvergleich import vergleichen, referenz_fuer
FROZEN = 'bestand_20261016_100035_d963e3'
REFERENCE = pfad(ROOT, 'Daten/Referenz_Seminararbeit/analyse_20261022_171939_db9a9f')

def reproduzieren(finbert_neu=False, vollstaendig=False, fortschritt=print, return_type=None):
    from Programm.grundlagen.konfiguration import laden
    from Programm.grundlagen.laufkennungen import kennung
    from Programm.grundlagen.json_dateien import speichern
    from Programm.grundlagen.laufkennungen import zeit
    from Programm.projektpruefung.dateiinventar import pruefen
    from Programm.transkripte.pruefung import pruefen as transkripte_pruefen
    from Programm.transkripte.rekonstruktion import rekonstruieren
    fortschritt('1/6 Eingefrorene Dateien und Transkriptverknüpfungen prüfen …')
    inventory = pruefen(vollstaendig)
    transcripts = transkripte_pruefen(vollstaendig)
    cfg = laden()
    if return_type is not None:
        cfg = dict(cfg, return_type=return_type)
    reference = referenz_fuer(cfg['return_type'])
    reference_cfg = json.loads(pfad(reference, 'manifest.json').read_text(encoding='utf-8'))['config']
    for k, v in reference_cfg.items():
        if k not in {'download_trends', 'download_transcripts'} and cfg[k] != v:
            raise ValueError('Die Einstellungen weichen von der gewählten Renditereferenz ab: ' + k)
    expected = json.loads(pfad(ROOT, 'requirements-Versionen.json').read_text(encoding='utf-8'))
    from importlib.metadata import version
    mismatch = {k: {'expected': v, 'actual': version(k)} for k, v in expected.items() if version(k) != v}
    if sys.version_info[:2] != (3, 12) or mismatch:
        raise ValueError('Für den Referenzlauf Python 3.12 und die festgelegten Pakete verwenden: ' + repr(mismatch))
    work = pfad(pfad(ROOT, 'Daten/bestaende'), kennung('bestand'))
    work.mkdir(parents=True, exist_ok=False)
    run_cfg = dict(cfg, bestand=work.name)
    run_cfg.update(download_trends=False, download_transcripts=False)
    fortschritt('2/6 Separaten Arbeitsbestand anlegen; Originaleingaben bleiben erhalten …')
    shutil.copytree(pfad(pfad(pfad(ROOT, 'Daten/bestaende'), FROZEN), 'roh'), pfad(work, 'roh'))
    from Programm.grundlagen.pfade import rohbestand_gliedern
    rohbestand_gliedern(work)
    if not finbert_neu:
        shutil.copy2(pfad(pfad(pfad(ROOT, 'Daten/bestaende'), FROZEN), 'finbert_cache.csv'), pfad(work, 'finbert_cache.csv'))
    speichern(pfad(work, 'bestand.json'), {'art': 'Reproduktion', 'created_at': zeit(), 'basisbestand': FROZEN, 'config': run_cfg, 'network': False, 'finbert_new_inference': finbert_neu})
    from Programm.datenaufbereitung.aufbereitung import verarbeiten
    from Programm.sentiment.auswertung import auswerten
    from Programm.berechnung.berechnung import berechnen
    from Programm.statistik.auswertung import regressieren
    with ohne_netzwerk():
        fortschritt('3/6 Kurse, EPS, Trends und vollständige Transkripte neu aufbereiten …')
        verarbeiten(run_cfg, fortschritt)
        fortschritt('4/6 Satztrennung, gespeicherte Satzbewertungen und TONE neu zusammenführen …' if not finbert_neu else '4/6 Alle Sätze mit dem lokalen FinBERT-Modell neu bewerten …')
        auswerten(run_cfg, fortschritt)
        fortschritt('5/6 CAR und Einflussgrößen berechnen; Regressionen und Grafiken erstellen …')
        berechnen(run_cfg, fortschritt)
        result = regressieren(run_cfg, fortschritt)
        output = pfad(pfad(ROOT, 'Daten/ergebnisse'), result['ordner'])
        fortschritt('6/6 Ergebnisse mit der gewählten Renditereferenz vergleichen …')
        comparison = vergleichen(output, reference)
    _, rebuilt = rekonstruieren()
    report = {'created_at': zeit(), 'passed': True, 'input_verification': inventory, 'transcripts': transcripts, 'transcript_reconstruction': rebuilt, 'comparison': comparison, 'return_type': cfg['return_type'], 'reference': reference.relative_to(ROOT).as_posix(), 'inference': 'FinBERT vollständig neu ausgeführt' if finbert_neu else 'Eingefrorene FinBERT-Satzvorhersagen wiederverwendet; Satzidentitäten, Texte und Modellrevision werden geprüft; TONE erneut berechnet.', 'network_used': False, 'python': sys.version, 'packages': {k: version(k) for k in expected}, 'working_dataset': work.relative_to(ROOT).as_posix(), 'output': output.relative_to(ROOT).as_posix()}
    speichern(pfad(output, 'Reproduktionspruefung.json'), report)
    speichern(pfad(ROOT, 'Daten/letzte_reproduktion.json'), report)
    from Programm.ausgabe.verzeichnis import aktualisieren
    aktualisieren()
    fortschritt('BESTANDEN: 170 Ereignisse, 113 Datumscluster und alle 12 Referenztabellen stimmen überein; Renditeart: ' + cfg['return_type'])
    fortschritt('Bericht: ' + str(pfad(output, 'bericht.html')))
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--finbert-neu', action='store_true', help='Alle ca. 80.000 Sätze erneut inferieren; erheblich längerer Lauf. Zusätzliche Pakete benötigt.')
    p.add_argument('--vollstaendig', action='store_true', help='Auch Audios und Modellgewichte vollständig hashen.')
    p.add_argument('--renditen', choices=['simple', 'log'], help='Renditeart; Standard aus einstellungen.json. log reproduziert den historischen Lauf.')
    a = p.parse_args()
    try:
        reproduzieren(a.finbert_neu, a.vollstaendig, return_type=a.renditen)
    except Exception as e:
        print('REPRODUKTION NICHT BESTANDEN: ' + str(e), file=sys.stderr)
        return 1
    return 0
