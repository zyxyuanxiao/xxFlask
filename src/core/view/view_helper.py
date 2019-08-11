# -*- coding:utf-8 -*-

from src.core.utils import pb_tools, pbx
from src.core.view import view_builtin


class ApiRegHelper(object):
    def __init__(self, scope, api_prefix, *import_modules):
        self.scope = scope
        self.api_prefix = "/{}".format(api_prefix) if api_prefix else ""
        self._dict_api = {}
        reg_modules = list(import_modules)
        for m in reg_modules:
            for k, v in m.__dict__.iteritems():
                if isinstance(v, type) and issubclass(v, pbx.Message):
                    self.get_api_data_from_descriptor(k, v, v.DESCRIPTOR)
                elif isinstance(v, pbx.EnumDescriptor):
                    self.get_api_enum_from_descriptor(v.name, v)

    def get_api_enum_from_descriptor(self, name, descriptor):
        if descriptor.has_options:
            opts = descriptor.GetOptions().ListFields()
            dic = dict()
            dic['urls'] = ''
            dic['view'] = ''
            dic['methods'] = []
            dic['ec'] = 'TODO'
            dic['descriptor'] = descriptor
            dic['disable_log'] = False
            for f, d in opts:
                dic[f.name] = d
            dic['comment'] = dic['ec']
            self._dict_api[name] = dic

    def get_api_data_from_descriptor(self, name, message, descriptor):
        if descriptor.has_options:
            opts = descriptor.GetOptions().ListFields()
            dic = dict()
            dic['urls'] = ''
            dic['view'] = ''
            dic['methods'] = []
            dic['comment'] = 'TODO'
            dic['descriptor'] = descriptor
            dic['disable_log'] = False
            for f, d in opts:
                dic[f.name] = d
            self._dict_api[name] = dic

    def help_data(self):
        help_dict = {}
        for k, dic in self._dict_api.iteritems():
            dic_help = dict()
            dic_help['api_name'] = k
            dic_help['api_view'] = dic['view'] if len(dic['view']) > 0 else 'None'
            dic_help['api_comment'] = dic['comment']
            dic_help['api_urls'] = dic['urls'].split(',') if len(dic['urls']) > 0 else []
            dic_help['data_orig'] = pb_tools.descriptor_to_dict(dic['descriptor'], False)
            dic_help['data_other_orig'] = pb_tools.descriptor_inner_type_to_dict(dic['descriptor'], False)
            dic_help['data_camel'] = pb_tools.descriptor_to_dict(dic['descriptor'], True)
            dic_help['data_other_camel'] = pb_tools.descriptor_inner_type_to_dict(dic['descriptor'], True)
            dic_help['methods'] = dic['methods']
            dic_help['api_type'] = 'Enum' if isinstance(dic['descriptor'], pbx.EnumDescriptor) else 'Message'
            help_dict[k] = dic_help
        return help_dict

    def reg_api_views(self, reg_callback, reg_kwargs, current_setting, *modules):
        def find_type(view_name):
            if len(view_name) > 0:
                for x in modules:
                    if x.__dict__.has_key(view_name):
                        return x.__dict__.get(view_name)
                msg = 'cannot find view {}'.format(view_name)
                # raise Exception(msg)
                # print msg
            return None

        for k, dic in self._dict_api.iteritems():
            urls = dic['urls'].split(',')
            view = dic['view']
            comment = dic['comment']
            url_list = map(lambda x: "{}{}".format(self.api_prefix, x.strip()), urls)
            view_type = find_type(view)
            if view_type:
                dic['methods'] = view_type and view_type.methods
                # kwargs = {'debug':current_setting.DEBUG}
                kwargs = {'debug': True}
                kwargs.update(dic)
                # restful_api.add_resource(view_type, *url_list,resource_class_kwargs=kwargs)
                reg_callback(view_type, *url_list, resource_class_kwargs=kwargs)
                print dic['descriptor'].name, url_list, view.encode('utf-8')

        self.reg_builtin_api_views(reg_callback, reg_kwargs)

    def reg_builtin_api_views(self, reg_callback, reg_kwargs):
        self.reg_builtin_api_help_views(reg_callback, reg_kwargs)
        # self.RegBuiltinApiInfoViews(reg_callback, reg_kwargs)
        # self.RegBuiltinApiTimeViews(reg_callback, reg_kwargs)
        # self.RegBuiltinApiLogLevelViews(reg_callback, reg_kwargs)
        # self.RegBuiltinApiMyIpViews(reg_callback, reg_kwargs)
        # self.RegBuiltinApiModelsViews(reg_callback, reg_kwargs)
        # self.RegBuiltinApiRestableViews(reg_callback, reg_kwargs)
        # self.RegBuiltinApiDBStatusViews(reg_callback, reg_kwargs)
        # InfoView.current_setting = current_setting
        # ModelDetailInfoView.APP_NAME = current_setting.APP_NAME

    def reg_builtin_api_help_views(self, reg_callback, reg_kwargs):
        url_list = ["{}/help/".format(self.api_prefix), "{}/help/<string:api_name>/".format(self.api_prefix)]
        reg_callback(view_builtin.ApiBuiltinHelpView, *url_list,
                     resource_class_args=[self.api_prefix, self.help_data()])

    # def RegBuiltinApiInfoViews(self, reg_callback, reg_kwargs):
    #     view_builtin.ApiBuiltinInfoView.INFO = reg_kwargs.get('INFO', None)
    #     url_list = ["{}/info/".format(self.api_prefix), "{}/Info/".format(self.api_prefix)]
    #     reg_callback(view_builtin.ApiBuiltinInfoView, *url_list)
    #
    # def RegBuiltinApiTimeViews(self, reg_callback, reg_kwargs):
    #     url_list = ["{}/time/".format(self.api_prefix), "{}/time/<int:target_time>".format(self.api_prefix)]
    #     reg_callback(view_builtin.ApiBuiltinTimeView, *url_list)
    #
    # def RegBuiltinApiLogLevelViews(self, reg_callback, reg_kwargs):
    #     url_list = []
    #     url_list.append("{}/loglevel/".format(self.api_prefix))
    #     url_list.append("{}/loglevel/<string:loglevel_type>/".format(self.api_prefix))
    #     url_list.append("{}/loglevel/<string:loglevel_type>/<int:loglevel>/".format(self.api_prefix))
    #     reg_callback(view_builtin.ApiBuiltinLogLevelView, *url_list)
    #
    # def RegBuiltinApiMyIpViews(self, reg_callback, reg_kwargs):
    #     url_list = ["{}/myip/".format(self.api_prefix)]
    #     reg_callback(view_builtin.ApiBuiltinMyIpView, *url_list)
    #
    # def RegBuiltinApiModelsViews(self, reg_callback, reg_kwargs):
    #     url_list = []
    #     url_list.append("{}/models/".format(self.api_prefix))
    #     url_list.append("{}/models/<string:name>/".format(self.api_prefix))
    #     url_list.append("{}/models/<string:name>/<string:key>/".format(self.api_prefix))
    #     reg_callback(view_builtin.ApiBuiltinModelsView, *url_list)
    #
    # def RegBuiltinApiRestableViews(self, reg_callback, reg_kwargs):
    #     url_list = []
    #     url_list.append("{}/restable/".format(self.api_prefix))
    #     url_list.append("{}/restable/<string:name>/".format(self.api_prefix))
    #     reg_callback(view_builtin.ApiBuiltinRestableView, *url_list)
    #
    # def RegBuiltinApiDBStatusViews(self, reg_callback, reg_kwargs):
    #     url_list = []
    #     url_list.append("{}/db-status/".format(self.api_prefix))
    #     url_list.append("{}/db-status/<string:name>/".format(self.api_prefix))
    #     reg_callback(view_builtin.ApiBuiltinDBStatusView, *url_list)
