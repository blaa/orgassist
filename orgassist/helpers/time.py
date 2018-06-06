"""
Abstract access to the datetime so it will be easier to implement timezones
later.
"""

import pytz
import datetime as dt

class Time:
    """
    Time related helpers
    """
    def __init__(self, timezone='UTC'):
        self.timezone = pytz.timezone(timezone)

    def now(self):
        "Return current time with local timezone"
        local_time = dt.datetime.now()
        return self.timezone.localize(local_time)

    def normalize(self, date):
        "Normalize given date to main date"
        return self.timezone.normalize(date)
