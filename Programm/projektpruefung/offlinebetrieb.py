"""projektpruefung · offlinebetrieb – klar abgegrenzter Projektbaustein."""
from contextlib import contextmanager
import os, socket

@contextmanager
def ohne_netzwerk():
    """Auch versehentliche Downloadversuche abbrechen, statt frische Daten zu mischen."""
    original = socket.socket.connect
    previous = {key: os.environ.get(key) for key in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE']}
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')

    def blocked(*args, **kwargs):
        raise RuntimeError('Die Reproduktion ist offline; Netzwerkzugriff wurde blockiert.')
    socket.socket.connect = blocked
    try:
        yield
    finally:
        socket.socket.connect = original
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
