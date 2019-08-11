# -*- coding:utf-8 -*-

import time
import copy
import flask
import ujson as json
from flask import request
from src.core.view.view import APIViewBase, APIView


class ApiBuiltinHelpView(APIViewBase):
    def __init__(self, *args, **kwargs):
        super(ApiBuiltinHelpView, self).__init__()
        self.scope = args[0]
        self._help = args[1]

    def get(self, api_name=None):
        url_root = request.url_root + self.scope
        camel = False
        index = False
        if request.args.has_key('camel'):
            camel = request.args['camel'] == 'true'
        if request.args.has_key('index'):
            index = request.args['index'] == 'true'

        def remove_nouse(h):
            h.pop('data_orig')
            h.pop('data_other_orig')
            h.pop('data_camel')
            h.pop('data_other_camel')

        if api_name is None:
            help_list = copy.deepcopy(list(self._help.itervalues()))
            help_list.sort(key=lambda x: x['api_name'])
            api_list = []
            if index:
                api_list.extend([h['api_name'] for h in help_list])
            if camel:
                for h in help_list:
                    h['data'] = h['data_camel']
                    h['data_other'] = h['data_other_camel']
            else:
                for h in help_list:
                    h['data'] = h['data_orig']
                    h['data_other'] = h['data_other_orig']

            for h in help_list:
                remove_nouse(h)

            ret_obj = {}
            if index:
                ret_obj['api'] = api_list
            else:
                ret_obj['api'] = help_list
        else:
            h = {}
            r = self._help.get(api_name, {})
            if r:
                h = copy.deepcopy(r)
                if camel:
                    h['data'] = h['data_camel']
                    h['data_other'] = h['data_other_camel']
                else:
                    h['data'] = h['data_orig']
                    h['data_other'] = h['data_other_orig']
                remove_nouse(h)
            ret_obj = {}
            ret_obj['api'] = h

        ret_obj['version'] = '1.1.0.0'
        resp = flask.make_response(json.dumps(ret_obj), 200)
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        request.disable_log = True
        return resp


class ApiBuiltinMyIpView(APIView):
    def get(self):
        ret = {}
        ret["myip"] = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        return self.make_response(ret)
