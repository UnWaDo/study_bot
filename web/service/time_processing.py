from datetime import datetime, date, timedelta
import pytz


TIME_ZONE = pytz.timezone('Europe/Moscow')
DATE_FORMAT = '%d-%m-%Y'
DATETIME_FORMAT = '%H:%M:%S %Z %d-%m-%Y'
SITE_DATETIME_FORMAT = '%Y-%m-%dT%H:%M'
WEEK_DAYS = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
TIME_FORMAT = '%H:%M'
WEEK_EVEN = ['o', 'e', 'u']


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

def format_time(time, format=TIME_FORMAT):
    return time.strftime(format)

def format_birth_date(date):
    return date.strftime(DATE_FORMAT)

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

def parse_datetime(string, format):
    try:
        dt = datetime.strptime(string, format)
        return dt
    except ValueError:
        return None

def parse_week_day(day):
    try:
        return WEEK_DAYS.index(day.lower())
    except ValueError:
        return None

def get_week_day(index):
    return WEEK_DAYS[index%7]
