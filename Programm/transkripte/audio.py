"""transkripte · audio – klar abgegrenzter Projektbaustein."""

def zeitbereich(text):

    def seconds(s):
        value = 0.0
        for part in s.strip().replace(',', '.').split(':'):
            value = value * 60 + float(part)
        return value
    a, b = text.split('–')
    return (seconds(a), seconds(b))
