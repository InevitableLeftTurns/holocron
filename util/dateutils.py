"""
Description: function(s) for parsing string dates into datetime
"""
import datetime


def string_to_date(instr):
    return string_to_datetime(instr).date()


def string_to_datetime(instr):
    if not instr:
        raise ValueError('Empty string passed into datetime conversion')
    return datetime.datetime.strptime(instr, "%Y-%m-%dT%H:%M:%S" )


def datetime_to_string(indate, dtformat=None):
    return indate.isoformat()


def date_to_string(indate, dtformat=None):
    strftimeformat = dtformat or "%Y-%m-%d"
    return indate.strftime(strftimeformat)


def min_date():
    """
    minimum date for the system for easy identification of the min date
    """
    return datetime.datetime(1900, 1, 1)  # Sadly Pickett's Charge has been retired due to strftime limitations


def max_date():
    """
    maximum date for the system for easy identification of the max date
    """
    return datetime.datetime(3000, 12, 31)


