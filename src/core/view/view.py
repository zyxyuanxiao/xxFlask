# -*- coding:utf-8 -*-

import flask
import lz4.frame
import ujson as json
from flask import request
import flask_restful.reqparse
from src.core.utils import pb_tools, pbx
from src.core.log import *


class APIViewBase(flask_restful.Resource):
    def __init__(self, *args, **kwargs):
        super(APIViewBase, self).__init__()


default_parser = flask_restful.reqparse.RequestParser()
default_parser.add_argument('byid', type=int, location='args', trim=True)


class APIView(APIViewBase):
    HEADER_TOKEN = 'Token'
    HEADER_TOKEN_LEN = len(HEADER_TOKEN) + 1
    HEADER_ACCOUNT_TOKEN = 'AccountToken'
    HEADER_ACCOUNT_TOKEN_LEN = len(HEADER_ACCOUNT_TOKEN) + 1
    HEADER_SESSION = 'Session'
    HEADER_SESSION_LEN = len(HEADER_SESSION) + 1
    EXTEND_CLS = None

    def __init__(self, *args, **kwargs):
        super(APIView, self).__init__(*args, **kwargs)
        self.debug = kwargs.get('debug', True)
        self.args = None
        self.disable_log = kwargs.get('disable_log', False)
        self.post_cache = kwargs.get('post_cache', True)
        request.debug = self.debug
        request.disable_log = self.disable_log
        request.post_cache = self.post_cache

    def get_arg(self, key, default=None):
        if not hasattr(self, 'args'):
            self.args = default_parser.parse_args(request)
        return self.args.get(key) or default

    def parse_pb_request(self, cls_pb):
        req_obj = cls_pb()
        error_msg = None
        req_user_id = "0"
        req_method = ""
        req_seq = -1
        req_path = ""
        req_ipaddr = ""
        req_rawdata = ""

        try:
            req_user_id = request.user_id if request.user_id else "0"
            req_method = request.method
            req_seq = request.seq
            req_path = request.path
            req_ipaddr = request.ipaddr
            req_rawdata = request.data if request.data else ""
        except Exception as e:
            error_msg = str(e)
            res_data_log_str = "PARAM_EXCEPTION_REQ_DATA_{}_{},SEQ_{},{},{},{},ERRMSG={}".format(req_user_id,
                                                                                                 req_method, req_seq,
                                                                                                 req_path, req_ipaddr,
                                                                                                 len(req_rawdata),
                                                                                                 error_msg)
            ERROR(res_data_log_str)

        try:
            req_data = request.data
            if request.headers.get('content-encoding') == "lz4":
                req_data = lz4.frame.decompress(request.data)

            if request.data and request.data != 'null':
                if request.headers.get('content-type') == 'application/wireformat':
                    req_obj.ParseFromString(req_data)
                else:
                    pbx.json_format.Parse(req_data, req_obj, True)
        except Exception as e:
            error_msg = str(e)
            req_data_log_str = "EXCEPTION_REQ_DATA_{}_{},SEQ_{},{},{},{},ERRMSG={}".format(req_user_id, req_method,
                                                                                           req_seq, req_path,
                                                                                           req_ipaddr, len(req_rawdata),
                                                                                           error_msg)
            ERROR(req_data_log_str)
            return req_obj, False, error_msg

        if not self.disable_log:
            req_data_log_str = "REQ_DATA_{}_{},SEQ_{},{},{},{},DATA_OBJ={}".format(req_user_id, req_method, req_seq,
                                                                                   req_path, req_ipaddr,
                                                                                   len(req_rawdata), req_obj)
            INFO(req_data_log_str)

        return req_obj, True, error_msg

    @staticmethod
    def get_token(self):
        if 'Authorization' in request.headers:
            authstr = request.headers['Authorization']
            if authstr.startswith(APIView.HEADER_TOKEN):
                token = authstr[APIView.HEADER_TOKEN_LEN:]
                return token.strip()
        return ''

    @staticmethod
    def get_session(self):
        if 'Authorization' in request.headers:
            authstr = request.headers['Authorization']
            if authstr.startswith(APIView.HEADER_SESSION):
                token = authstr[APIView.HEADER_SESSION_LEN:]
                return token.strip()
        return ''

    @staticmethod
    def get_account_token(self):
        if 'Authorization' in request.headers:
            authstr = request.headers['Authorization']
            if authstr.startswith(APIView.HEADER_ACCOUNT_TOKEN):
                token = authstr[APIView.HEADER_ACCOUNT_TOKEN_LEN:]
                return token.strip()
        return ''

    def pack_json_with_debug(self, result_key, res_dic, page_info, debugdic):
        result_dic = res_dic.get(result_key, res_dic)
        dic = {result_key: pb_tools.mix_to_dict(result_dic)}
        if self.debug and debugdic:
            result_debug_dic = debugdic.get('debug', debugdic)
            dic['debug'] = pb_tools.mix_to_dict(result_debug_dic)
        if page_info:
            dic['pageInfo'] = pb_tools.mix_to_dict(page_info)
        return json.dumps(dic)

    def __pack_json_with_debug_nokey(self, res_dic, page_info, debugdic):
        dic = pb_tools.mix_to_dict(res_dic)
        if self.debug and debugdic:
            result_debug_dic = debugdic.get('debug', debugdic)
            dic['debug'] = pb_tools.mix_to_dict(result_debug_dic)
        if page_info:
            dic['pageInfo'] = pb_tools.mix_to_dict(page_info)
        return json.dumps(dic)

    def flask_response_by_json(self, ret_json, disable_log, http_code):
        response = self.make_encode_response(ret_json, http_code)
        response.headers["Content-Type"] = 'application/json'
        return response

    def __make_response_json(self, ret, http_code, **debugdic):
        ret_dict = ret if isinstance(ret, dict) else dict(result=ret)
        ret_json = self.pack_json_with_debug('result', ret_dict, None, debugdic)
        disalbelog = debugdic.get('disable_log', False)
        return self.flask_response_by_json(ret_json, disalbelog, http_code)

    def make_response(self, ret, http_code=200, **debugdic):
        if request.headers.get('accept') == 'application/wireformat':
            return self.__make_response_pb(ret, http_code, **debugdic)
        else:
            return self.__make_response_json(ret, http_code, **debugdic)

    def make_encode_response(self, data, http_code):
        if request.headers.get('accept-encoding') == 'lz4' and self.EXTEND_CLS and self.EXTEND_CLS.IsLZ4Enable(
                len(data)):
            data_compressed = lz4.frame.compress(data, 0)
            response = flask.make_response(data_compressed, http_code)
            response.headers["Content-Encoding"] = 'lz4'
        else:
            response = flask.make_response(data, http_code)
        return response

    def __make_response_pb(self, ret, http_code, **debugdic):
        if self.EXTEND_CLS:
            ret_obj = self.EXTEND_CLS.GeneratePbObject(ret, http_code, debugdic)
        else:
            return self.__make_response_json(ret, http_code, **debugdic)

        data = ret_obj.SerializeToString()
        response = self.make_encode_response(data, http_code)
        response.headers["Content-Type"] = 'application/wireformat'
        return response

    def make_response_message_box(self, code, error="", **debugdic):
        if self.EXTEND_CLS:
            ret_obj = self.EXTEND_CLS.GenerateMessageBoxResponseObject(code, error, debugdic)
        else:
            ret_obj = {'notify': 'NOT SUPPORT'}

        ret_dic = pb_tools.pb_to_dict(ret_obj)
        ret_json = self.pack_json_with_debug('notify', ret_dic, None, debugdic)
        disalbelog = debugdic.get('disable_log', False)
        ERROR("Error Important ,Code:{},Error:{}".format(ret_obj.notify.code, error))
        return self.flask_response_by_json(ret_json, disalbelog, 507)

    def make_response_message_box_with_ban(self, code, ban_reason, ban_time):
        return self.make_response_message_box(code, ban_reason, ban_reason=ban_reason, ban_time=ban_time)

    def make_response_kick(self, code, **debugdic):
        if self.EXTEND_CLS:
            ret_obj = self.EXTEND_CLS.GenerateKickResponseObject(code, "", debugdic)
        else:
            ret_obj = {'kick': 'NOT SUPPORT'}

        ret_dic = pb_tools.pb_to_dict(ret_obj)
        ret_json = self.pack_json_with_debug('kick', ret_dic, None, debugdic)
        return self.flask_response_by_json(ret_json, False, 510)

    def make_response_scroll(self, code, error="", **debugdic):
        if self.EXTEND_CLS:
            ret_obj = self.EXTEND_CLS.GenerateScrollResponseObject(code, error, debugdic)
        else:
            ret_obj = {'notify': 'NOT SUPPORT'}

        ret_dic = pb_tools.pb_to_dict(ret_obj)
        ret_json = self.pack_json_with_debug('notify', ret_dic, None, debugdic)
        disalbelog = debugdic.get('disable_log', False)
        ERROR("Error Important ,Code:{},Error:{}".format(ret_obj.notify.code, error))
        return self.flask_response_by_json(ret_json, disalbelog, 509)
