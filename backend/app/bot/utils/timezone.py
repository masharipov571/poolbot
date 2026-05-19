import datetime

def get_uz_time() -> datetime.datetime:
    """
    Returns current datetime in Uzbekistan Time (UTC + 5).
    """
    return datetime.datetime.utcnow() + datetime.timedelta(hours=5)

def to_uz_time(dt: datetime.datetime) -> datetime.datetime:
    """
    Converts a UTC datetime to Uzbekistan Time (UTC + 5).
    """
    if not dt:
        return None
    return dt + datetime.timedelta(hours=5)

def format_uz_time(dt: datetime.datetime) -> str:
    """
    Converts a UTC datetime to Uzbekistan local time and formats it beautifully.
    """
    if not dt:
        return ""
    uz_dt = to_uz_time(dt)
    return uz_dt.strftime("%Y-%m-%d %H:%M:%S")
