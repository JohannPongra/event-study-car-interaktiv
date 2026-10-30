"""Die festgelegten FinBERT-Dateien aus der Originalquelle laden und prüfen."""
from pathlib import Path
import hashlib

REVISION = '4921590d3c0c3832c0efea24c8381ce0bda7844b'
REPOSITORY = 'yiyanghkust/finbert-tone'
HASHES = {
    'config.json': 'd52a95795ddc4409275c570cfef8fd81770b54d9aaa40c8750a32af1680962f6',
    'pytorch_model.bin': 'f31c2036e91c9854bcc35141d16669dd07b9726adfe391d1011bff1de7ea4b32',
    'vocab.txt': '85f2481b4e3c25a7ece5e0e4930631a75c1a5fe2d31b0ecd9b5d51136ab98de8',
}


def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bereitstellen(root=None, progress=print):
    from huggingface_hub import hf_hub_download
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    target = root / 'Daten/Modelle/FinBERT' / REVISION
    target.mkdir(parents=True, exist_ok=True)
    for filename, expected in HASHES.items():
        file = target / filename
        if file.is_file() and checksum(file) == expected:
            continue
        progress('FinBERT aus der festgelegten Originalquelle laden: ' + filename)
        hf_hub_download(repo_id=REPOSITORY, revision=REVISION, filename=filename,
                        local_dir=str(target), force_download=True)
        if checksum(file) != expected:
            raise ValueError('FinBERT-Prüfsumme stimmt nicht überein: ' + filename)
    progress('FinBERT-Modellversion und alle drei Prüfsummen bestätigt.')
    return target


if __name__ == '__main__':
    bereitstellen()
