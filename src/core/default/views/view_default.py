from src.core.view.view import APIView
from src.core.default.protocol.default_pb2 import *


class AutoFightCommandView(APIView):

    def get(self):
        print 'this is test'
        resp = ApiTest.resp()
        resp.success = True
        return self.make_response(resp)
