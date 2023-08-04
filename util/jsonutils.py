import json
import datetime

from data.Tip import Tip
from util import dateutils


class JsonContextEncoder(json.JSONEncoder):
    """
    Encodes the input dictionary into a JSON object, using the underlying toJson
    call for any NodeObjects
    """

    def __init__(self, datetimeformat=None, dateformat=None, **kwargs):
        super(JsonContextEncoder, self).__init__(**kwargs)
        self.datetimeformat = datetimeformat
        self.dateformat = dateformat

    def default(self, obj):
        if isinstance(obj, Tip):
            return obj.to_json()

        if isinstance(obj, datetime.datetime):
            return dateutils.datetime_to_string(obj, self.datetimeformat)

        if isinstance(obj, datetime.date):
            return dateutils.date_to_string(obj, self.dateformat)

        if isinstance(obj, set):
            return list(obj)

        raise TypeError('Unable to convert object {0} to JSON'.format(obj))
