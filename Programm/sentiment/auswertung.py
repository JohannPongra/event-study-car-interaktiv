"""sentiment · auswertung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.sentiment.satzidentitaeten import satzdaten
from Programm.sentiment.vorhersagecache import cache_laden
from Programm.sentiment.inferenz import vorhersagen
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.standardwerte import MODELL
from Programm.sentiment.satztrennung import SATZTRENNUNG_VERSION
from Programm.grundlagen.pfade import bestand_ordner
from Programm.grundlagen.konfiguration import einstellungen
from Programm.grundlagen.tabellen import lesen
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.sentiment.tonalitaet import tonwert
from Programm.grundlagen.laufkennungen import zeit

def auswerten(werte=None, fortschritt=print):
    cfg = einstellungen(werte)
    folder = bestand_ordner(cfg)
    schreibziel_pruefen(folder)
    out = pfad(folder, 'aufbereitet')
    file = pfad(out, 'transcripts.csv')
    if not file.exists():
        raise ValueError('Zuerst python -m Programm aufbereiten ausführen.')
    texts = lesen(file)
    sentences = satzdaten(texts, cfg)
    cache_file = pfad(folder, 'finbert_cache.csv')
    cached = cache_laden(cache_file)
    missing = sentences.loc[~sentences.sentence_id.isin(cached.sentence_id)]
    cached = vorhersagen(missing, cached, cache_file, cfg, fortschritt)
    scored = sentences.merge(cached, on='sentence_id', how='left', validate='one_to_one')
    counts = scored.groupby(['event_id', 'label']).size().unstack(fill_value=0).reindex(columns=['positive', 'negative', 'neutral'], fill_value=0)
    counts.columns = ['n_positive', 'n_negative', 'n_neutral']
    counts['n_sentences'] = counts.sum(axis=1)
    counts['tone'] = [tonwert(row.n_positive, row.n_negative, row.n_neutral) for row in counts.itertuples()]
    counts['tone_source'] = 'FinBERT: vollständiger Call, alle Sprecher'
    counts['model'], counts['revision'] = (MODELL, cfg['finbert_revision'])
    schreiben(scored, pfad(out, 'finbert_saetze.csv'))
    schreiben(counts.reset_index(), pfad(out, 'tone.csv'))
    speichern(pfad(out, 'finbert.json'), {'created_at': zeit(), 'model': MODELL, 'revision': cfg['finbert_revision'], 'transcripts_sha256': pruefsumme(file), 'tone_sha256': pruefsumme(pfad(out, 'tone.csv')), 'sentences': len(scored), 'ties': 'neutral vor positive vor negative', 'sentence_split': SATZTRENNUNG_VERSION})
    fortschritt(f'Tonalität für {len(counts)} Calls gespeichert.')
    return {'calls': len(counts), 'saetze': len(scored)}
