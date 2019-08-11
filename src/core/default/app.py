# -*- coding:utf-8 -*-
import sys

sys.path.append('/xxFlask/')

from src.core.server import wsgi
from src.core.default import settings

wsgi_app = wsgi.launch(CONFIG=settings.Config)


def debug_run():
    import gevent.pool
    import gevent.wsgi
    worker_pool = gevent.pool.Pool(settings.Config.WSGI_SPAWN_POOL_SIZE)
    real_server = gevent.wsgi.WSGIServer((settings.Config.HOST,
                                          settings.Config.PORT),
                                         settings.Config.APP_NAME,
                                         spawn=worker_pool)
    if real_server is None:
        assert settings.Config.APP_NAME + ' wsgi server init error'
        return
    real_server.serve_forever()


if __name__ == "__main__":
    wsgi_app.run()
