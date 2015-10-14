import logging.config

LOGGING_CONFIG = {
    'version': 1,
    # 'disable_existing_loggers': False,
    'formatters': {
        'void': {
            'format': ''
        },
        'standard': {
            'format': '%(asctime)-15s %(levelname)s %(name)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'cherrypy_ws': {
            'level': 'DEBUG',
            'class': 'efos.logger.WSHandler',
            'formatter': 'standard',
            # 'stream': 'ext://sys.stdout'
        },
        'cherrypy_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'void',
            'stream': 'ext://sys.stdout'
        },
        'cherrypy_access': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'void',
            'filename': 'access.log',
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        },
        'cherrypy_error': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'void',
            'filename': 'errors.log',
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'cherrypy_ws'],
            'level': 'DEBUG'
        },
        'db': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'ws4py': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': False
        },
        'cherrypy.access': {
            'handlers': ['cherrypy_access'],
            'level': 'INFO',
            'propagate': False
        },
        'cherrypy.error': {
            'handlers': ['cherrypy_console', 'cherrypy_error'],
            'level': 'INFO',
            'propagate': False
        },
    }
}
logging.config.dictConfig(LOGGING_CONFIG)
