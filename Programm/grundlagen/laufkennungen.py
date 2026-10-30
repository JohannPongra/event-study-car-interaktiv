"""grundlagen · laufkennungen – klar abgegrenzter Projektbaustein."""
from datetime import datetime
import uuid

def zeit():
    return datetime.now().astimezone().isoformat(timespec='seconds')

def kennung(prefix):
    return prefix + '_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
