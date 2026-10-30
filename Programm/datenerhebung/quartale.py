"""datenerhebung · quartale – klar abgegrenzter Projektbaustein."""
from datetime import date

def geschaeftsquartal(day, end_month):
    day = date.fromisoformat(day)
    quarter = ((day.month - end_month) % 12 - 1) % 12 // 3 + 1
    year = day.year + int(day.month > end_month)
    return f'{year}Q{quarter}'
