# -*- coding:utf-8 -*-

from src.core.utils import pbx


class ModelField(object):
    def __init__(self):
        self._property = None
        self._scope_name = None
        self.real_key = None

    # init will be called when models init
    def init(self, model_type):
        pass


class CounterField(ModelField):
    FUNCTION_KEY = 'counter_field'

    def __init__(self, init_count=0, scope_name=None):
        super(CounterField, self).__init__()
        self._name = scope_name
        self._init_count = init_count

    def init(self, model_type):
        self._name = self._name or model_type.__name__

    @property
    def name(self):
        return self._name

    @property
    def init_count(self):
        return self._init_count


class BaseKeyField(ModelField):
    FUNCTION_KEY = 'key_field'

    @property
    def name(self):
        return self._property

    def build_real_key(self, key):
        return '{}:{{{}}}'.format(self._scope_name, key)

    def __str__(self):
        return "{}:{{key}}".format(self._scope_name)

    @property
    def pb_key(self):
        return False


class DynamicKeyField(BaseKeyField):
    def __init__(self, scope_name=None):
        super(DynamicKeyField, self).__init__()
        self._scope_name = scope_name

    def init(self, model_type):
        if self._scope_name:
            pass
        else:
            df = model_type.data_field
            self._scope_name = df._cls.__name__

    def __str__(self):
        return "DynamicKey:{}:{{key}}".format(self._scope_name)
        # print 'dynamic key scope {}'.format(self._scope_name)


class StaticKeyField(BaseKeyField):
    def __init__(self, key_str, scope_name=None):
        super(StaticKeyField, self).__init__()
        self._scope_name = scope_name
        self._property = key_str

    def init(self, model_type):
        if not self._scope_name:
            df = model_type.data_field
            self._scope_name = df._cls.__name__

        self.real_key = '{}:{{{}}}'.format(self._scope_name, self._property)
        print 'static key {}'.format(self.real_key)

    def __str__(self):
        return "StaticKey:{}".format(self.real_key)

    def build_real_key(self, _=None):
        return self.real_key

    @property
    def name(self):
        return None


class KeyField(BaseKeyField):
    FUNCTION_KEY = 'key_field'

    def __init__(self, prop, scope_name=None):
        super(KeyField, self).__init__()
        self._property = prop
        self._scope_name = scope_name

    def init(self, model_type):
        if not self._scope_name:
            df = model_type.data_field
            self._scope_name = df._cls.__name__

    def build_real_key(self, key):
        return '{}:{{{}}}'.format(self._scope_name, key)

    @property
    def pb_key(self):
        return True


class ExpireField(ModelField):
    FUNCTION_KEY = 'expire_field'

    def __init__(self, prop):
        super(ExpireField, self).__init__()
        self._property = prop

    @property
    def name(self):
        return self._property


class DbField(ModelField):
    FUNCTION_KEY = 'db_field'

    def __init__(self, dbname):
        super(DbField, self).__init__()
        self._dbname = dbname

    @property
    def name(self):
        return self._dbname


class DataField(ModelField):
    FUNCTION_KEY = 'data_field'

    def __init__(self, data_cls):
        super(DataField, self).__init__()
        self._cls = data_cls
        # print cls,type(cls)
        if isinstance(data_cls, type):
            self.is_pb_msg = issubclass(data_cls, pbx.Message)
            if self.is_pb_msg:
                self._to_string_func = lambda x: x.SerializeToString()

                def from_string(data_str):
                    obj = data_cls()
                    obj.MergeFromString(data_str)
                    return obj

                self._from_string_func = from_string

                self.pb_fields_dict = data_cls.DESCRIPTOR.fields_by_name
            else:
                if data_cls is bool:
                    self._to_string_func = lambda obj: '1' if obj else '0'
                    self._from_string_func = lambda data_str: True if data_str == '1' else False
                elif data_cls is str:
                    self._to_string_func = lambda s: s
                    self._from_string_func = lambda s: s
                else:
                    self._to_string_func = lambda obj: str(obj)
                    self._from_string_func = lambda data_str: data_cls(data_str)

    @property
    def fields_dict(self):
        return self.pb_fields_dict

    def create_data(self):
        return self._cls()

    def data_cls(self):
        return self._cls

    def to_string(self, obj):
        return self._to_string_func(obj)

    def from_string(self, data_str):
        return self._from_string_func(data_str)

    def set_func(self, to_string, from_string):
        self._to_string_func = to_string
        self._from_string_func = from_string
