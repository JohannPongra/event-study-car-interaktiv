"""sentiment · kontext · auswertung – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from Programm.grundlagen.pfade import pfad
from Programm.sentiment.kontext.abschnitte import GEWICHT_SHA256
from Programm.sentiment.kontext.abschnitte import KLASSEN
from Programm.sentiment.kontext.abschnitte import MODELL
from Programm.sentiment.kontext.abschnitte import MODELLORDNER
from Programm.sentiment.kontext.abschnitte import REGEL
from Programm.sentiment.kontext.abschnitte import REVISION
from Programm.sentiment.satztrennung import SATZTRENNUNG_VERSION
from Programm.sentiment.kontext.abschnitte import abschnitte
from Programm.sentiment.kontext.aggregierung import aggregieren
from Programm.grundlagen.pfade import bestand_ordner
from Programm.sentiment.kontext.abschnitte import identitaet
from Programm.grundlagen.konfiguration import laden
from Programm.grundlagen.tabellen import lesen
import numpy as np
import pandas as pd
from Programm.grundlagen.pruefsummen import pruefsumme
from Programm.sentiment.satztrennung import saetze
from Programm.grundlagen.tabellen import schreiben
from Programm.grundlagen.json_dateien import speichern
from Programm.grundlagen.laufkennungen import zeit

def auswerten(werte=None, fortschritt=print):
    cfg = laden() if werte is None else werte
    folder = bestand_ordner(cfg)
    schreibziel_pruefen(folder)
    file = pfad(pfad(folder, 'aufbereitet'), 'transcripts.csv')
    if not file.exists():
        raise ValueError('Zuerst Transkripte aufbereiten.')
    if not pfad(MODELLORDNER, 'model.safetensors').exists() or pfad(MODELLORDNER, 'model.safetensors').stat().st_size < 1000000:
        raise ValueError('Die festgelegten finbert-lc-Gewichte fehlen oder sind unvollständig: ' + str(MODELLORDNER))
    if pruefsumme(pfad(MODELLORDNER, 'model.safetensors')) != GEWICHT_SHA256:
        raise ValueError('Die lokalen Gewichte entsprechen nicht der festgelegten veröffentlichten Revision.')
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(MODELLORDNER, local_files_only=True, trust_remote_code=False)
    tokenzahl = lambda text: len(tokenizer.encode(text, add_special_tokens=True, truncation=False, verbose=False))
    rows = {'lc_sentence': [], 'lc_context': []}
    for turn in lesen(file).sort_values(['event_id', 'turn_index']).itertuples():
        sentences = saetze(turn.content)
        for variant, blocks in [('lc_sentence', [(i, i, s) for i, s in enumerate(sentences)]), ('lc_context', abschnitte(sentences, tokenzahl))]:
            for first, last, text in blocks:
                length = tokenzahl(text)
                if length > 512:
                    raise ValueError(f'finbert-lc: überlanger Text in {turn.event_id}, Satz {first}.')
                rows[variant].append({'unit_id': identitaet(text), 'event_id': turn.event_id, 'turn_index': turn.turn_index, 'sentence_first': first, 'sentence_last': last, 'n_sentences': last - first + 1, 'tokens': length, 'text': text})
    frames = {k: pd.DataFrame(v) for k, v in rows.items()}
    if any((frame.empty for frame in frames.values())):
        raise ValueError('Keine Texte für finbert-lc vorhanden.')
    units = pd.concat(frames.values(), ignore_index=True).drop_duplicates('unit_id')
    cache_file = pfad(folder, 'finbert_lc_cache.csv')
    cache = lesen(cache_file) if cache_file.exists() else pd.DataFrame(columns=['unit_id', 'label', 'p_neutral', 'p_positive', 'p_negative'])
    if cache.unit_id.duplicated().any():
        raise ValueError('Doppelte Einheit im finbert-lc-Cache.')
    if not cache.empty:
        p = cache[['p_neutral', 'p_positive', 'p_negative']].to_numpy(float)
        if not np.isfinite(p).all() or (p < 0).any() or (not np.allclose(p.sum(axis=1), 1, atol=1e-05)) or (not np.array_equal(np.array(KLASSEN)[p.argmax(axis=1)], cache.label)):
            raise ValueError('Ungültige Vorhersagen im finbert-lc-Cache.')
    missing = units.loc[~units.unit_id.isin(cache.unit_id)].sort_values('tokens', kind='stable')
    fortschritt(f"finbert-lc: {len(frames['lc_sentence'])} Sätze, {len(frames['lc_context'])} Abschnitte; {len(missing)} neue eindeutige Eingaben.")
    out = pfad(pfad(folder, 'aufbereitet'), 'kontext')
    schreiben(frames['lc_context'], pfad(out, 'kontext_abschnitte.csv'))
    if not missing.empty:
        model = AutoModelForSequenceClassification.from_pretrained(MODELLORDNER, local_files_only=True, trust_remote_code=False, use_safetensors=True)
        model.eval()
        torch.manual_seed(0)
        names = {str(name).lower(): int(index) for index, name in model.config.id2label.items()}
        if set(names) != set(KLASSEN) or model.config.max_position_embeddings != 512:
            raise ValueError('Unerwartete Konfiguration der finbert-lc-Gewichte.')
        order = [names[k] for k in KLASSEN]
        start, batches, predictions = (0, 0, [])
        while start < len(missing):
            batch_size = 64 if int(missing.iloc[start].tokens) <= 128 else 16
            batch = missing.iloc[start:start + batch_size]
            inputs = tokenizer(batch.text.tolist(), padding=True, truncation=False, return_tensors='pt')
            with torch.inference_mode():
                probabilities = torch.softmax(model(**inputs).logits, dim=1).cpu().numpy()[:, order]
            for row, probs in zip(batch.itertuples(), probabilities):
                predictions.append({'unit_id': row.unit_id, 'label': KLASSEN[int(probs.argmax())], **dict(zip(['p_neutral', 'p_positive', 'p_negative'], probs))})
            start += len(batch)
            batches += 1
            if batches % 50 == 0 or start == len(missing):
                new_predictions = pd.DataFrame(predictions)
                cache = new_predictions if cache.empty else pd.concat([cache, new_predictions], ignore_index=True)
                predictions = []
                schreiben(cache, cache_file)
                fortschritt(f'finbert-lc: {start} von {len(missing)} neuen eindeutigen Eingaben')
    for variant, frame in frames.items():
        scored = frame.merge(cache, on='unit_id', how='left', validate='many_to_one')
        if scored.label.isna().any():
            raise ValueError('Vorhersagen fehlen.')
        name = 'lc_saetze.csv' if variant == 'lc_sentence' else 'lc_abschnitte.csv'
        schreiben(scored, pfad(out, name))
        schreiben(aggregieren(scored, variant), pfad(out, 'tone_' + variant + '.csv'))
    names = ['kontext_abschnitte.csv', 'lc_saetze.csv', 'lc_abschnitte.csv', 'tone_lc_sentence.csv', 'tone_lc_context.csv']
    speichern(pfad(out, 'manifest.json'), {'created_at': zeit(), 'model': MODELL, 'revision': REVISION, 'sentence_split': SATZTRENNUNG_VERSION, 'rule': REGEL, 'maximum_tokens_including_special': 512, 'transcripts_sha256': pruefsumme(file), 'nsp_used': False, 'weighting': 'number of original sentences, hard class; neutral included', 'classes': {'0': 'negative', '1': 'neutral', '2': 'positive'}, 'model_files': {p.name: pruefsumme(p) for p in MODELLORDNER.iterdir() if p.is_file()}, 'files': {n: pruefsumme(pfad(out, n)) for n in names}})
    fortschritt('finbert-lc: Satz- und Kontexttonalität vollständig gespeichert.')
    return {'calls': frames['lc_sentence'].event_id.nunique(), 'sentences': len(frames['lc_sentence']), 'sections': len(frames['lc_context'])}
