import logging
from datetime import datetime


class WaveTapLogger(logging.Logger):
    """
    Configure logger format.

    Custom logger for the project with a specific format:
    [YYYY-MM-DD HH:MM:SS.ss][<Object>][<Debug Level>]: <Logger Message>
    """

    def __init__(self, name):
        super().__init__(name)
        handler = logging.StreamHandler()
        handler.setFormatter(WaveTapLogFormatter())
        self.addHandler(handler)
        self.setLevel(logging.INFO)


class WaveTapLogFormatter(logging.Formatter):
    """Logger formatter object."""

    def __init__(self):
        # Set the format string with placeholders
        super().__init__(
            fmt="[%(asctime)s][%(name)s][%(levelname)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S.%f",
        )

    def formatTime(self, record, datefmt=None):
        """Format time for log entries."""
        time = datetime.fromtimestamp(record.created)
        # Format: YYYY-MM-DD HH:MM:SS.sss
        return time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def get_wt_logger(name):
    """Get a project logger with the custom format."""
    logging.setLoggerClass(WaveTapLogger)
    return logging.getLogger(name)
