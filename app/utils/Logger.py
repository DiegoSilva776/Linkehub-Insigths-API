# -*- coding: utf-8 -*-

"""
Logger.py contains variables and methods that are useful for loggin info out of
the system into different data sources.
"""

# Imports
import sys
import time
import datetime
sys.path.append("../")

from datetime import datetime
from datetime import timedelta

class Logger:

    """
        Return a timestamp of the current time in the ISO 8601 format
    """
    def get_utc_iso_timestamp(self):
        return self.iso_8601_format(datetime.now())

    """
        Return a timestamp of the current time + a period of time, a timeout in the ISO 8601 format
    """
    def get_utc_iso_timestamp_plus_timeout(self):
        today = datetime.now()
        end_date = today + timedelta(hours=1)

        return self.iso_8601_format(end_date)

    """
        YYYY-MM-DDThh:mm:ssTZD (1997-07-16T19:20:30-03:00)
    """
    def iso_8601_format(self, dt):
        if dt is None:
            return ""

        fmt_datetime = dt.strftime('%Y-%m-%dT%H:%M:%S')

        time_zone = str.format('{0:+06.2f}', -float(time.altzone) / 3600)

        if time_zone is None:
            time_zone = "+00:00"

        return fmt_datetime + time_zone
