"""datenaufbereitung · validierung – klar abgegrenzter Projektbaustein."""

def eindeutig(frame, columns, name):
    if frame.duplicated(columns).any():
        raise ValueError(name + ': doppelte Schlüssel. Quelle zuerst bereinigen.')
