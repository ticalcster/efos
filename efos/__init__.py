import logging
import logging.config
import os
import importlib

import configargparse

__version__ = '0.1.1'

__all__ = ('log', 'get_options', 'get_handlers')

EFOS_SIG = '^efos\d#[cmnr]{0,4}#'

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
        'efos_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': 'efos.log',
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
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
            'handlers': ['default'],
            'level': 'DEBUG'
        },
        'efos': {
            'handlers': ['cherrypy_ws', 'efos_file'],
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
log = logging.getLogger('efos')


def get_handlers(options):
    print(__name__, 'Getting Handlers')
    handlers = []
    for handler in get_handler_classes(options):
        handlers.append(handler(options))
    return handlers


def get_handler_classes(options):
    handler_classes = []
    if options.handlers:
        for handler in options.handlers:
            module_name, class_name = handler.rsplit(".", 1)
            handler_module = importlib.import_module(module_name)
            handler_class = getattr(handler_module, class_name)
            handler_classes.append(handler_class)
    return handler_classes


def get_options():
    # Config / Arg stuffs
    cap = configargparse.ArgParser(default_config_files=['efos.conf', ],
                                   allow_unknown_config_file_keys=True)
    cap.add_argument('-a', '--archive', default="archive", help='directory to archive files')
    cap.add_argument('-c', '--config', is_config_file=True, help='path to config file')
    cap.add_argument('-d', '--delete', action="store_true", help='delete files after processing')
    cap.add_argument('--delay', default=0, type=int,
                     help='added a delay between getting notified and processing the file')
    cap.add_argument('-f', '--file-format', default="%(filename)s", help='filename format from kwargs in QRCode')
    #cap.add_argument('--handlers', action="append", default=[],
    cap.add_argument('--handlers', nargs='+', default=['efos.handler.FileHandler', 'efos.handler.HttpHandler'],
                     help='handlers to use when processing parsed files')
    cap.add_argument('-l', '--log-level', default=11, type=int, help='logging level [1-50+]')
    cap.add_argument('-p', '--port', default=8081, type=int, help='web server port')
    cap.add_argument('-w', '--watch', required=True, help='directory to watch for files')

    #  nargs='+',
    # 'efos.handler.FileHandler', 'efos.handler.HttpHandler'

    options, nope = cap.parse_known_args()

    print('----', options.handlers)

    # adds the options from each active handler
    for handler_class in get_handler_classes(options):
        handler_class.add_arguments(cap)

    options = cap.parse_args()

    # set logging level
    log = logging.getLogger('efos')
    log.setLevel(options.log_level)

    log.info(options.handlers)

    if options.archive:
        if not os.path.isabs(options.archive):
            options.archive = os.path.join(options.watch, options.archive)

    return options
