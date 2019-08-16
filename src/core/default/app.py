# -*- coding:utf-8 -*-
import sys

sys.path.append('/workspace/')

from src.core.server import wsgi
from src.core.default import settings

wsgi_app = wsgi.launch(CONFIG=settings.Config)
server_app = wsgi_app.server_app


def debug_run():
    wsgi_app.debug_run()


if __name__ == "__main__":
    wsgi_app.run()
