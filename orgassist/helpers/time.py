"""
Abstract access to the datetime so it will be easier to implement timezones
later.
"""

import datetime as dt

class Time:
    """
    Time related helpers
    """
    def __init__(self, timezone='local'):
        self.timezone = timezone

    @staticmethod
    def now():
        "Return current time with local timezone"
        # TODO: Timezones
        return dt.datetime.now()
