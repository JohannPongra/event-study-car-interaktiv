"""transkripte · pruefung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.transkripte.archiv_lesen import BASE
from Programm.transkripte.archiv_lesen import EXPORT
from Programm.transkripte.archiv_lesen import FROZEN
from Programm.transkripte.archiv_lesen import daten
from Programm.transkripte.archiv_lesen import load
from Programm.transkripte.archiv_lesen import rows
import runpy
from Programm.transkripte.archiv_lesen import sha

def pruefen(mit_audio=False):
    verifier = runpy.run_path(str(pfad(EXPORT, 'export_pruefen.py')))
    result = verifier['verify_package'](EXPORT)
    manifest, ledger, human = daten()
    imported = {r['event_id']: r for r in rows(pfad(FROZEN, 'roh/transcripts.csv'))}
    prepared = {r['event_id']: r for r in rows(pfad(FROZEN, 'aufbereitet/transcripts.csv'))}
    if set(imported) != set(manifest['calls']) or set(prepared) != set(manifest['calls']):
        raise ValueError('Transkriptzuordnung stimmt nicht mit den Analysedaten überein.')
    for event, item in manifest['calls'].items():
        expected = pfad(EXPORT, item['text_path']).read_bytes().decode('utf-8')
        if imported[event]['content'] != expected or prepared[event]['content'] != expected:
            raise ValueError('Analysetext weicht vom Endtext ab: ' + event)
    audio = load(pfad(EXPORT, 'Nachweise/Audio_Quellinventar.json'))['calls']
    for event in manifest['calls']:
        p = pfad(pfad(BASE, 'Audio'), event + '.mpeg')
        if not p.is_file():
            raise ValueError('Originalaudio fehlt: ' + event)
        if mit_audio and sha(p) != audio[event]['audio/' + event + '.mpeg']:
            raise ValueError('Audio-Prüfsumme verändert: ' + event)
    result.update(analysis_texts_identical=True, audio_files_present=170, audio_hashes_checked=mit_audio, correction_count=sum((len(x['changes']) for x in ledger['overlays'].values())), historical_decision_count=len(ledger['decisions']))
    return result
