from datetime import datetime, date, timedelta
import pytz


TIME_ZONE = pytz.timezone('Europe/Moscow')
DATE_FORMAT = '%d-%m-%Y'
DATETIME_FORMAT = '%H:%M:%S %Z %d-%m-%Y'
SITE_DATETIME_FORMAT = '%Y-%m-%dT%H:%M'


def is_week_even(dt=None):
    if dt is None:
        dt = date.today()
    first_monday_in_sem = date(2020, 9, 1) - timedelta(date(2020, 9, 1).weekday())
    delta = dt - first_monday_in_sem
    sem_week = (delta.days // 7) + 1
    if sem_week % 2:
        return False
    else:
        return True

def format_datetime(dt, format=DATETIME_FORMAT):
    utc = pytz.utc.localize(dt)
    return utc.astimezone(TIME_ZONE).strftime(format)

def format_date(date, format=DATE_FORMAT):
    utc = pytz.utc.localize(date)
    return utc.astimezone(TIME_ZONE).strftime(format)

def get_current_datetime(format=SITE_DATETIME_FORMAT):
    utc = pytz.utc.localize(datetime.utcnow())
    return utc.astimezone(TIME_ZONE).strftime(format)

def parse_and_transform(dt, format=SITE_DATETIME_FORMAT, tz=TIME_ZONE):
    dt = datetime.strptime(dt, format)
    dt = to_utc(dt, tz).replace(tzinfo=None)
    return dt

def to_utc(dt, tz=TIME_ZONE):
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc)
