from Programm.sentiment.modell_laden import modell_laden
import pandas as pd
from Programm.grundlagen.tabellen import schreiben

def vorhersagen(missing, cached, cache_file, cfg, fortschritt=print):
    if missing.empty:
        return cached
    predictions = []
    tokenizer, model, order, maximum, torch = modell_laden(cfg, fortschritt)
    lengths = missing.text.map(lambda text: len(tokenizer.encode(text, add_special_tokens=True, truncation=False)))
    if lengths.gt(maximum).any():
        row = missing.loc[lengths.gt(maximum)].iloc[0]
        raise ValueError(f'Satz überschreitet {maximum} Tokens: {row.event_id}, Beitrag {row.turn_index}, Satz {row.sentence_index}. Satztrennung prüfen; Text wird nicht abgeschnitten.')
    missing = missing.loc[lengths.sort_values(kind='stable').index]
    batch_size = cfg['finbert_batch_size']
    for start in range(0, len(missing), batch_size):
        batch = missing.iloc[start:start + batch_size]
        inputs = tokenizer(batch.text.tolist(), padding=True, truncation=False, return_tensors='pt')
        with torch.inference_mode():
            probabilities = torch.softmax(model(**inputs).logits, dim=1).cpu().numpy()[:, order]
        for row, probabilities_row in zip(batch.itertuples(), probabilities):
            label = ['neutral', 'positive', 'negative'][int(probabilities_row.argmax())]
            predictions.append({'sentence_id': row.sentence_id, 'label': label, **dict(zip(['p_neutral', 'p_positive', 'p_negative'], probabilities_row))})
        if start % (batch_size * 100) == 0:
            fortschritt(f'FinBERT: {min(start + batch_size, len(missing))} von {len(missing)} neuen Sätzen')
            combined = pd.DataFrame(predictions) if cached.empty else pd.concat([cached, pd.DataFrame(predictions)], ignore_index=True)
            schreiben(combined, cache_file)
    cached = pd.DataFrame(predictions) if cached.empty else pd.concat([cached, pd.DataFrame(predictions)], ignore_index=True)
    schreiben(cached, cache_file)
    return cached
