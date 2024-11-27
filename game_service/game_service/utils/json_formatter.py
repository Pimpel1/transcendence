import logging
import json


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'sender': record.name,
            'loglevel': record.levelname,
            'message': record.getMessage(),
        }
        return json.dumps(log_entry)
