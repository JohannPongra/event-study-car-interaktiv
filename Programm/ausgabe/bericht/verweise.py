"""Relative Links an die gegliederte Ergebnisablage anpassen."""
from Programm.grundlagen.pfade import pfad
from pathlib import Path
import html, os, re
from urllib.parse import urlsplit, unquote

def verweise(text, vorher, nachher):

    def ersetzen(match):
        value = html.unescape(match.group(2))
        url = urlsplit(value)
        if url.scheme or url.netloc or (not url.path) or value.startswith(('/', 'javascript:')):
            return match.group(0)
        old = (Path(vorher).parent / unquote(url.path)).resolve()
        target = pfad(old)
        rel = os.path.relpath(target, Path(nachher).parent).replace(os.sep, '/')
        if url.query:
            rel += '?' + url.query
        if url.fragment:
            rel += '#' + url.fragment
        return match.group(1) + html.escape(rel, quote=True) + match.group(3)
    return re.sub('((?:href|src)=["\\\'])([^"\\\']*)(["\\\'])', ersetzen, text)

def bericht_speichern(out, text):
    target = pfad(out, 'bericht.html')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(verweise(text, Path(out).joinpath('bericht.html'), target), encoding='utf-8')
