import logging
import logging.config
import sys


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s] [%(process)d] %(module)s: %(message)s',
            'datefmt': r"%Y-%m-%d %H:%M:%S %z",
        },
    },
    'handlers': {
        'consoleHandler': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        '': {
            'handlers': ['consoleHandler'],
            'level': 'DEBUG',
        },
        'rakomqtt': {
            'handlers': ['consoleHandler'],
            'level': 'DEBUG',
            'propagate': 0,
        },
    }
}


class AppLogger:
    def __init__(self):
        self._logger = self.configure_logging()

    @staticmethod
    def configure_logging():
        logging.config.dictConfig(LOGGING)
        return logging.getLogger('rakomqtt')

    def debug(self, *args, **kwargs):
        self._logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self._logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        self._logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        # exc_info=True is needed for the exception to be available in the json formatter
        self._logger.error(*args, **kwargs, exc_info=True)

    def critical(self, *args, **kwargs):
        self._logger.critical(*args, **kwargs, exc_info=True)

    def exception(self, *args, **kwargs):
        self._logger.exception(*args, **kwargs, exc_info=True)


logger = AppLogger()
