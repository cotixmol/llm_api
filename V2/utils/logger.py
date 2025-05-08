"""
Usage example:

```py
from src.utils.logger import logger

logger.error(f"some_debug_code: {s.MY_STR}" , extra= {"n_docs":23})
```

> will output (in a single line log)

```json
{
    "level": "ERROR",
    "msg": "some_debug_code: ",
    "n_docs": 23,
    "timestamp": "2023-10-11T06:12:08.573657+00:00"
}
```
"""

import logging
from pythonjsonlogger import jsonlogger
from api.config.secrets import settings as s


logger = logging.getLogger()

lvl = {"debug": 10, "info": 20, "warning": 30, "error": 40, "critical": 50}
logger.setLevel(lvl[s.LOG_LEVEL.lower()])
logHandler = logging.StreamHandler()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["msg"] = record.message


formatter = CustomJsonFormatter("%(level)s %(msg)s", timestamp=True)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
