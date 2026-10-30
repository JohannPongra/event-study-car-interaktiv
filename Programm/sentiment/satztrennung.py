"""sentiment · satztrennung – klar abgegrenzter Projektbaustein."""
import re
SATZTRENNUNG_VERSION = 'english_rules_v1'
ABBREVIATIONS = {'mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sr.', 'jr.', 'st.', 'vs.', 'approx.', 'fig.', 'no.', 'nos.', 'jan.', 'feb.', 'mar.', 'apr.', 'jun.', 'jul.', 'aug.', 'sep.', 'sept.', 'oct.', 'nov.', 'dec.'}
CONTINUING_ABBREVIATIONS = {'inc.', 'corp.', 'co.', 'ltd.', 'etc.', 'e.g.', 'i.e.'}
SENTENCE_STARTERS = {'we', 'our', 'i', 'it', 'this', 'that', 'the', 'these', 'they', 'he', 'she', 'you', 'next', 'however', 'thank', 'thanks'}
ASCII_TOKEN = frozenset('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.')
NEXT_WORD = re.compile('[A-Za-z]+')

def saetze(text):
    """Deterministic English boundary rules; preserve every non-whitespace char.

    Numbers such as 3.5 and abbreviations/initialisms are protected. Boundaries
    require punctuation followed by whitespace or end of turn. Unpunctuated
    end-of-turn text is retained and flagged for review, never silently dropped.
    This is a reproducible heuristic, not a claim of perfect linguistic parsing.
    """
    text = str(text)
    rows = []
    start = 0
    for match in re.finditer('[.!?]+["\'”’\\)\\]]*(?=\\s|$)', text):
        end = match.end()
        token_end = match.start() + 1
        token_start = token_end
        while token_start and text[token_start - 1] in ASCII_TOKEN:
            token_start -= 1
        token = text[token_start:token_end]
        following = NEXT_WORD.search(text, end)
        next_word = following.group() if following else ''
        if match.group().startswith('.') and next_word:
            if token.lower() in ABBREVIATIONS:
                continue
            if token.lower() in CONTINUING_ABBREVIATIONS and next_word.lower() not in SENTENCE_STARTERS:
                continue
            if re.fullmatch('[A-Z]\\.', token) and (not re.fullmatch('&[A-Z]\\.', text[max(0, token_end - 3):token_end])):
                continue
            if re.fullmatch('(?:[A-Za-z]\\.){2,}', token) and next_word.lower() not in SENTENCE_STARTERS:
                continue
        left = start
        while left < end and text[left].isspace():
            left += 1
        if left < end:
            rows.append(text[left:end])
        start = end
    left = start
    while left < len(text) and text[left].isspace():
        left += 1
    end = len(text.rstrip())
    if left < end:
        rows.append(text[left:end])
    if ''.join((re.sub('\\s', '', s) for s in rows)) != re.sub('\\s', '', text):
        raise ValueError('Satztrennung hat Text verloren.')
    return rows
