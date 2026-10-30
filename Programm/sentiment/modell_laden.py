from Programm.grundlagen.pfade import pfad
from Programm.grundlagen.pfade import ORDNER

def modell_laden(cfg, fortschritt=print):
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
    except ImportError:
        raise ValueError('FinBERT-Abhängigkeiten fehlen. INSTALLIEREN_FINBERT.bat ausführen.') from None
    fortschritt('Festgelegtes lokales FinBERT-Modell laden; kein Download …')
    local_model = pfad(pfad(ORDNER, 'Modelle'), 'finbert-tone-' + cfg['finbert_revision'])
    if not local_model.is_dir():
        raise ValueError('Das festgelegte lokale FinBERT-Modell fehlt; keine automatische andere Modellversion geladen.')
    tokenizer = AutoTokenizer.from_pretrained(str(local_model), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(local_model), local_files_only=True)
    model.eval()
    torch.manual_seed(0)
    names = {str(name).lower(): int(index) for index, name in model.config.id2label.items()}
    if set(names) != {'neutral', 'positive', 'negative'}:
        raise ValueError('FinBERT liefert unerwartete Klassen.')
    order = [names[name] for name in ['neutral', 'positive', 'negative']]
    maximum = int(model.config.max_position_embeddings)
    return (tokenizer, model, order, maximum, torch)
