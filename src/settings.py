# -*- coding:utf-8 -*-


class Config(object):
    app_name = 'default'
    debug = False
    host = '0.0.0.0'
    port = 8008
    threaded = False
    wsgi_spawn_pool_size = 100
    debug_back_door = 5000
    local_log = True

    # DB
    db_check = False
    redis = [
        {
            'name': 'default_redis',
            'host': '0.0.0.0',
            'port': '7800',
            'password': '',
            'is_cluster': False,
        }
    ]

    # LOCK
    locker_expired = 20
    debug_lock = False

    # todo EXTENSIONS
    extensions = [
        {
            'extension_name': '',
            'extension_module': '',
            'extension_lazy_mode': '',
            'extension_tag': '',
        }
    ]

    # VIEW
    view_module = [
        {
            'file_dir': 'default',
            'file_prefix': 'view_',
            'module_prefix': 'default',
        }
    ]

    # MODEL
    model_module = [
        {
            'file_dir': 'default',
            'file_prefix': 'model_',
            'module_prefix': 'default',
        }
    ]

    # PROTOCOL
    protocol_module_info = [
        {
            'file_dir': 'protocol',
            'file_prefix': '',
            'file_suffix': 'pb2',
            'module_prefix': 'protocol',
        },
    ]


current = Config
