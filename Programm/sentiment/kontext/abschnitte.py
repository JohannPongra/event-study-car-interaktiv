"""sentiment · kontext · abschnitte – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import ORDNER
import hashlib
MODELL = 'ab30atsiwo/finbert-gpt-50agree'
REVISION = 'cddcf0cbc757e26443712bcacd92edbf3e00ef7a'
GEWICHT_SHA256 = '02959208a900f43f9816f5c84b2528d99d189ec7d07f83f74be1baf62f95a374'
MODELLORDNER = pfad(pfad(ORDNER, 'Modelle'), 'finbert-lc-' + REVISION)
REGEL = 'natural_order_whole_sentences_512_v1'
KLASSEN = ['neutral', 'positive', 'negative']
VARIANTEN = {'lc_sentence': 'finbert-lc: einzelne Sätze', 'lc_context': 'finbert-lc: natürliche Mehrsatzabschnitte, satzgewichtet'}

def abschnitte(sentences, tokenzahl, maximum=512):
    """Jeder Satz genau einmal, in Originalreihenfolge, ohne Kürzung."""
    result = []
    first, current = (0, [])
    for index, sentence in enumerate(sentences):
        if tokenzahl(sentence) > maximum:
            raise ValueError(f'Einzelner Satz {index} überschreitet {maximum} Tokens; keine Kürzung.')
        candidate = ' '.join([*current, sentence])
        if current and tokenzahl(candidate) > maximum:
            result.append((first, index - 1, ' '.join(current)))
            first, current = (index, [])
        current.append(sentence)
    if current:
        result.append((first, len(sentences) - 1, ' '.join(current)))
    covered = [i for first, last, _ in result for i in range(first, last + 1)]
    if covered != list(range(len(sentences))):
        raise ValueError('Abschnittsbildung hat Sätze verloren oder doppelt verwendet.')
    return result

def identitaet(text):
    return hashlib.sha256(f'{MODELL}|{REVISION}|{text}'.encode('utf-8')).hexdigest()
