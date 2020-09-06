from datetime import datetime, date, timedelta
import pytz


TIME_ZONE = pytz.timezone('Europe/Moscow')
DATE_FORMAT = '%d-%m-%Y'
DATETIME_FORMAT = '%H:%M:%S %Z %d-%m-%Y'


def is_week_even():
    first_monday_in_sem = date(2020, 9, 1) - timedelta(date(2020, 9, 1).weekday())
    delta = date.today()-first_monday_in_sem
    sem_week = (delta.days // 7) + 1
    if sem_week % 2:
        return False
    else:
        return True

def format_datetime(dt):
    utc = pytz.utc.localize(dt)
    return utc.astimezone(TIME_ZONE).strftime(DATETIME_FORMAT)

def format_date(date):
    utc = pytz.utc.localize(date)
    return utc.astimezone(TIME_ZONE).strftime(DATE_FORMAT)

def get_current_datetime(format=DATE_FORMAT):
    utc = pytz.utc.localize(datetime.utcnow())
    return utc.astimezone(TIME_ZONE).strftime(format)

def to_utc(dt, tz=TIME_ZONE):
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc)
