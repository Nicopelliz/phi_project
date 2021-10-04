from datetime import datetime, timedelta, timezone
import pytz
from pytz import timezone


def number_of_hours(date_input, input_tz):
    num_of_values = 24

    # data giorno dopo
    next_day = date_input + timedelta(1)

    # preparo le variabili timezone
    utc = pytz.utc
    input_timezone = timezone(input_tz)

    # creo la data localized
    loc_date = input_timezone.localize(date_input)
    loc_next_date = input_timezone.localize(next_day)

    # trasformo in UTC
    date_utc = loc_date.astimezone(utc)
    next_utc = loc_next_date.astimezone(utc)

    # controllo se ci sono differenze con l'orario del giorno dopo in UTC
    # se ci sono variazioni cambio il numero di ore
    hour_gap = date_utc.hour - next_utc.hour

    if hour_gap == -1:
        num_of_values = 23
    elif hour_gap == 1:
        num_of_values = 25

    return num_of_values


num = number_of_hours(datetime(2021, 3, 28, 00, 0, 0), 'europe/rome')

print(num)
