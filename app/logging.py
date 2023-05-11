import logging

from pydantic import BaseModel


class LogConfig(BaseModel):
    """
    Logging configuration
    """

    version = 1
    disable_existing_loggers = False
    formatters = {
        'default': {
            'fmt': '%(levelprefix)s %(asctime)s - %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    }
    handlers = {
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    }
    loggers = {
        '': {'handlers': ['default'], 'level': logging.INFO},
    }
