"""Statische Berichtsvorlagen mit bereits maskierten Inhalten füllen."""
from pathlib import Path
from string import Template

def vorlage_fuellen(name, werte):
    return Template(Path(__file__).with_name(name).read_text(encoding='utf-8')).substitute(werte)
