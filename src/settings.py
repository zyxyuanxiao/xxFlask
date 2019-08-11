# -*- coding:utf-8 -*-

class Config:
    APP_NAME = 'notifynew'
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 9010
    THREADED = False
    WSGI_SPAWN_POOL_SIZE = 100
    DEBUG_BACK_DOOR = 5000
    LOCAL_LOG = True

    REGION = "gl"

    MAX_TOKEN_AGE = 43200
    SECRET_KEY = '%/\xf3jIl\xf0\xd4\xdcR\xcf:\xac)R\x8dm\x1d*4,\xa8\x99\xac'

    DISPATCH_SERVER_URL = 'http://dockerhost:9006'

    # DB
    DB_CHECK = False
    REDIS = [
        {
            'NAME': 'cache_locker',
            'HOST': 'dockerhost',
            'PORT': '7800',
            'PASSWD': '',
            'ISCLUSTER': False,
        },
        {
            'NAME': 'cache_misc',
            'HOST': 'dockerhost',
            'PORT': '7800',
            'PASSWD': '',
            'ISCLUSTER': False,
        },
        {
            'NAME': 'ssd_misc',
            'HOST': 'dockerhost',
            'PORT': '7700',
            'PASSWD': '',
            'ISCLUSTER': False,
        }
    ]

    # LOCK
    LOCKER_EXPIRED = 20
    DEBUG_LOCK = False

    # EXTENSIONS
    EXTENSIONS = [
        {
            'EXTENSION_NAME': 'LAUNCHED_EXTENSION',
            'EXTENSION_MODULE': 'notifynew.launched_extension',
            'EXTENSION_LAZY_MODE': True,
            'EXTENSION_TAG': 'TAG_LAUNCHED',
        }
    ]

    # VIEW
    VIEW_MODULE_INFO = [
        {
            'FILE_DIR': 'notifynew',
            'FILE_PREFIX': 'view_',
            'FILE_SUFFIX': '',
            'MODULE_PREFIX': 'notifynew',
        }
    ]

    # MODEL
    MODEL_MODULE_INFO = [
        {
            'FILE_DIR': 'notifynew',
            'FILE_PREFIX': 'model_',
            'FILE_SUFFIX': '',
            'MODULE_PREFIX': 'notifynew',
        }
    ]

    # PROTOCOL
    PROTOCOL_MODULE_INFO = [
        {
            'FILE_DIR': 'protocol',
            'FILE_PREFIX': '',
            'FILE_SUFFIX': 'pb2',
            'MODULE_PREFIX': 'protocol',
        },
    ]


current = Config
