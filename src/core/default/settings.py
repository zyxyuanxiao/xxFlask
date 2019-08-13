# -*- coding:utf-8 -*-


class Config(object):
    APP_NAME = 'default'
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 7777
    THREADED = False
    WSGI_SPAWN_POOL_SIZE = 100
    DEBUG_BACK_DOOR = 5000
    LOCAL_LOG = True

    # DB
    DB_CHECK = False
    REDIS = [
        {
            'name': 'default_redis',
            'host': '0.0.0.0',
            'port': '7800',
            'password': '',
            'is_cluster': False,
        }
    ]

    # LOCK
    LOCKER_EXPIRED = 20
    DEBUG_LOCK = False

    # todo EXTENSIONS
    EXTENSIONS = [
        {
            'extension_name': '',
            'extension_module': '',
            'extension_lazy_mode': '',
            'extension_tag': '',
        }
    ]

    # VIEW
    VIEW_MODULE = [
        {
            'file_dir': '/workspace/src/core/default/views/',
            'file_prefix': 'view_',
            'module_prefix': 'views',
        }
    ]

    # MODEL
    MODEL_MODULE = [
        {
            'file_dir': '/workspace/src/core/default/models/',
            'file_prefix': 'model_',
            'module_prefix': '',
        }
    ]

    # PROTOCOL
    PROTOCOL_MODULE = [
        {
            'file_dir': '/workspace/src/core/default/protocol/',
            'file_prefix': '',
            'file_suffix': 'pb2',
            'module_prefix': 'protocol',
        },
    ]


current = Config
