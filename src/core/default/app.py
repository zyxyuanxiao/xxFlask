# -*- coding:utf-8 -*-
import sys

sys.path.append('/xxFlask/')

from src.core.server import wsgi
from src.core.default import settings

wsgi_app = wsgi.launch(CONFIG=settings.Config)

if __name__ == "__main__":
    wsgi_app.run()
