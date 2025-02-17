from datetime import datetime
from uvicorn.config import LOGGING_CONFIG
import logging
import os
import sys
from cortex.config import settings


# Get the default logging configuration from uvicorn and update it.
LOGGING_CONFIG["loggers"][__name__] = {
    "handlers": ["default"],
    "level": "INFO",
}
# Hide the access logs from the console.
LOGGING_CONFIG["loggers"]["uvicorn.access"] = {
    "handlers": ["default"],
    "level": "WARNING",
}
logging.config.dictConfig(LOGGING_CONFIG)


log = logging.getLogger()
if not os.path.exists(settings.log_dir):
    os.makedirs(settings.log_dir)
formatter = logging.Formatter(
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
stream_handler = logging.StreamHandler(sys.stdout)
log_filename = f"{settings.log_dir}/app_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_filename)
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
log.addHandler(file_handler)
# TODO: Specify the log level for different modules here, if needed.
log.setLevel(settings.log_level.upper())