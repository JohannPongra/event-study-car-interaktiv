"""grundlagen · pruefsummen – klar abgegrenzter Projektbaustein."""
from pathlib import Path
import hashlib

def pruefsumme(datei):
    digest = hashlib.sha256()
    with Path(datei).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
