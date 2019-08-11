# -*- coding:utf-8 -*-

import signal
import gevent
import gevent.backdoor
import flask
import flask_restful
import os
import sys
from src.core.log import *
from src.core.db import *
from src.core.utils import *
from src.core.model import *
from .serverstatus import ServerStatus


# import actkit.extensionkit as extensionkit
# import actkit.logkit as logkit
# import actkit.modelkit as modelkit
# import actkit.viewkit as viewkit
# import actkit.reskit as reskit
# import actkit.misckit as misckit
# import actkit.timekit as timekit
# from .serverstatus import ServerStatus

class BaseServerAppExtend(object):
    pass


class BaseServerApp(object):
    def __init__(self, **kwargs):
        reload(sys)
        sys.setdefaultencoding('utf8')
        super(BaseServerApp, self).__init__()
        self.app_extend_cls = None
        self.app_extend_obj = None
        self.kwargs = kwargs
        print "{}:BaseServerApp:__init__".format(type(self))
        print "{}-{}".format(type(self.kwargs), self.kwargs)

    def initialize(self):
        print "{}:BaseServerApp:Initialize".format(type(self))

    def set_extend(self, app_extend_cls):
        if app_extend_cls and isinstance(app_extend_cls, type) and issubclass(app_extend_cls, BaseServerAppExtend):
            self.app_extend_cls = app_extend_cls
            self.app_extend_obj = self.app_extend_cls()

    def launch(self):
        print "{}:Launch".format(type(self))


class WsgiServerAppExtend(BaseServerAppExtend):
    def before_first_request(self):
        pass

    def before_request(self):
        pass

    def teardown_request(self, ctx):
        pass

    def after_request(self, response):
        pass


class WsgiServerApp(BaseServerApp):
    def __init__(self, **kwargs):
        super(WsgiServerApp, self).__init__(**kwargs)

        self.server_config = self.kwargs.get('CONFIG')
        self.server_name = self.server_config.APP_NAME
        self.server_app = flask.Flask(self.server_name)
        self.server_app.config.from_object(self.server_config)
        self.server_app.debug = self.server_app.config['DEBUG']
        self.server_app.threaded = self.server_app.config['THREADED']
        self.host = self.server_app.config['HOST']
        self.port = self.server_app.config['PORT']
        self.restful_api = flask_restful.Api(self.server_app)
        self.real_server = None
        self.request_count = 0
        self.pool_size = self.server_config.wsgi_spawn_pool_size
        self.kill_count = 0
        self.consul_service_name = None
        self.consul = None
        self.log_helper = None
        self.server_time_offset = 0
        self.res_loader = None
        self.block_list = []
        self.server_app.url_map.strict_slashes = False
        self.health_url = "/{}/health/".format(self.server_name)
        print "{}:WsgiServerApp:__init__".format(type(self))

    def get_wsgi_app(self):
        return self.server_app

    def debug_run(self):
        import gevent.pool
        import gevent.wsgi
        worker_pool = gevent.pool.Pool(self.pool_size)
        self.real_server = gevent.wsgi.WSGIServer((self.host, self.port), self.server_app, spawn=worker_pool)
        if self.real_server is None:
            assert self.server_name + ' wsgi server init error'
            return
        self.real_server.serve_forever()

    def register_api(self, view_type, *url_list, **kwargs):
        self.restful_api.add_resource(view_type, *url_list, **kwargs)

    def initialize(self):
        ServerStatus.change(ServerStatus.INIT)
        super(WsgiServerApp, self).initialize()
        print "{}:WsgiServerApp:Initialize".format(type(self))
        print "{} -> {}".format(type(self.kwargs), self.kwargs)

        self.initialize_log()
        self.initialize_back_door()
        self.initialize_signal()
        self.initialize_route()

    def initialize_back_door(self):
        if not self.server_config.DEBUG_BACK_DOOR:
            return

        backdoor = gevent.backdoor.BackdoorServer(
            ('127.0.0.1', self.server_config.debug_back_door),
            banner="Hello from gevent backdoor!",
            locals={'foo': "From defined scope!"})
        print 'starting backdoor {}'.format(self.server_config.DEBUG_BACK_DOOR)
        gevent.spawn(backdoor.serve_forever)
        gevent.sleep(0.1)  # avoid backdoor start at worker in uwsgi enviroment.

    def initialize_log(self):
        local_log = getattr(self.server_config, "LOCAL_LOG", False)
        self.log_helper = LOGGING_INIT(self.server_name, local_log)

    def initialize_signal(self):
        gevent.signal(signal.SIGTERM, self.safe_shutdown)
        gevent.signal(signal.SIGALRM, self.safe_shutdown)

    def initialize_route(self):
        @self.server_app.before_first_request
        def before_first_request():
            # info('{} first request pid={}'.format(self.serverName,configClass.pid))
            self.before_first_request()

        @self.server_app.before_request
        def before_request():
            return self.before_request()

        @self.server_app.teardown_request
        def on_teardown(ctx):
            self.teardown_request(ctx)

        @self.server_app.after_request
        def after_request(response):
            return self.after_request(response)

    def before_first_request(self):
        print "BeforeFirstRequest"
        if self.app_extend_obj:
            self.app_extend_obj.before_first_request()

    def before_request(self):
        print "BeforeRequest"
        if self.app_extend_obj:
            return self.app_extend_obj.before_request()
        # return flask.make_response("OK", 200)

    def teardown_request(self, ctx):
        if self.app_extend_obj:
            self.app_extend_obj.teardown_request(ctx)

    def after_request(self, response):
        if self.app_extend_obj:
            self.app_extend_obj.after_request(response)
        return response

    def launch(self):
        super(WsgiServerApp, self).launch()
        self.initialize()
        self.start_server()
        self.launched()
        return self.get_wsgi_app()

    def launched(self):
        pass

    def safe_shutdown(self):
        pass

    def start_server(self):
        pass
        # info('{} server is starting....{} {}'.format(self.serverName,self.host,self.port))

        # ServerStatus.change(ServerStatus.OPEN)
        # if self.serverApp.config['SERVER_TIME_OFFSET']:
        #    gevent.spawn(ServerMiscInfo.get_time_offset)
        # self.serverApp.run(self.host,self.port)


class SmartServerApp(WsgiServerApp):
    def __init__(self, **kwargs):
        super(SmartServerApp, self).__init__(**kwargs)
        self.model_list = []
        self.view_module_list = []
        self.pb_list = []
        self.pb_dict = {}
        self.dbs = {}

    def initialize(self):
        super(SmartServerApp, self).initialize()
        self.initialize_base()
        self.initialize_extension()
        self.initialize_protocol()
        self.initialize_db()
        self.initialize_models()
        self.initialize_views()
        self.initialize_api()
        self.initialize_res()

    def initialize_base(self):
        INFO("InitializeBase")

    def initialize_extension(self):
        INFO("InitializeExtension")

    def initialize_db(self):
        INFO("InitializeDB")
        self.dbs.clear()
        dbs = redisx.create_db(self.server_config, self.log_helper)
        self.dbs.update(dbs)

    def load_modules(self, module_info_list, loaded_module_list, loaded_module_dict):
        print self.server_name
        for module_info in module_info_list:
            module_file_dir = module_info.get('FILE_DIR')
            module_file_prefix = module_info.get('FILE_PREFIX')
            module_prefix = module_info.get('MODULE_PREFIX')
            load_module_info_list = []

            for (parent_dir, sub_dirs, sub_files) in os.walk(module_file_dir):
                for sub_file in sub_files:
                    if sub_file.startswith(module_file_prefix) and sub_file.endswith(".py"):
                        load_module_name = "{}".format(sub_file.replace(".py", ""))
                        if module_prefix:
                            load_module_full_name = "{}.{}".format(module_prefix, load_module_name)
                        else:
                            load_module_full_name = load_module_name
                        load_module_info_list.append((load_module_full_name, load_module_name))
                break

            for (load_module_full_name, load_module_name) in load_module_info_list:
                print "try_import:{},{}".format(load_module_full_name, load_module_name)
                m = __import__(load_module_full_name, fromlist=[load_module_name])
                print "import success:{}".format(m)
                if loaded_module_list:
                    loaded_module_list.append(m)
                if loaded_module_dict:
                    loaded_module_dict[load_module_full_name] = m

    def dynamic_load(self, module_config_name, loaded_list=None, loaded_dict=None):
        module_info = getattr(self.server_config, module_config_name, None)
        if not module_info:
            return
        self.load_modules(module_info, loaded_list, loaded_dict)

    def initialize_models(self):
        print "InitializeModels"
        self.dynamic_load("model_module", self.model_list)
        ModelTypeBase.init_model_types(self.server_config, self.dbs)

    def initialize_views(self):
        print "InitializeViews"
        self.dynamic_load("view_module", self.view_module_list)

    def initialize_protocol(self):
        print "InitializeProtocol"
        self.dynamic_load("PROTOCOL_MODULE_INFO", self.pb_list, self.pb_dict)
        pb_tools.initialize(self.pb_dict)

    def initialize_res(self):
        print "InitializeRes"

    def initialize_api(self):
        print "InitializeAPI"
        api_prefix = getattr(self.server_config, "API_PREFIX", self.server_name)
        api_reg_helper = viewkit.ApiRegHelper(self.server_name, api_prefix, *self.pb_list)
        api_reg_helper.RegApiViews(self.register_api, {"INFO": self.server_config}, None, *self.view_module_list)

    def launched(self):
        print "Launched"
        super(SmartServerApp, self).launched()
        extensionkit.call_extension_tag("TAG_LAUNCHED", serverConfig=self.server_config)

        try:
            import uwsgidecorators
            @uwsgidecorators.postfork
            def on_uwsgi_post_fork():
                self.post_forked()
        except Exception as e:
            self.post_forked()

        ServerStatus.change(ServerStatus.OPEN)

    def post_forked(self):
        print "PostForked"
        extensionkit.call_extension_tag("TAG_POSTFORKED", serverConfig=self.server_config)


__app = None


def launch(**kwargs):
    global __app
    if __app:
        return

    __app = SmartServerApp(**kwargs)
    wsgi_app = __app.launch()
    return wsgi_app


def set_extend(app_extend_cls):
    if not __app:
        return
    __app.SetExtend(app_extend_cls)
