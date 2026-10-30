"""grundlagen · json dateien – klar abgegrenzter Projektbaustein."""
from Programm.grundlagen.pfade import schreibziel_pruefen
from pathlib import Path
import json

def json_sicher(wert):
    """NaN wird als JSON-null gespeichert, niemals als erfundene Null."""
    import math
    if isinstance(wert, dict):
        return {str(k): json_sicher(v) for k, v in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [json_sicher(v) for v in wert]
    if isinstance(wert, Path):
        return str(wert)
    if hasattr(wert, 'item'):
        return json_sicher(wert.item())
    if isinstance(wert, float) and (not math.isfinite(wert)):
        return None
    return wert

def speichern(datei, inhalt):
    schreibziel_pruefen(datei)
    datei = Path(datei)
    datei.parent.mkdir(parents=True, exist_ok=True)
    temp = datei.with_suffix(datei.suffix + '.tmp')
    temp.write_text(json.dumps(json_sicher(inhalt), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temp.replace(datei)
