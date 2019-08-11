# -*- coding:utf-8 -*-

from .modelFields import ModelField
from src.core.db import redisx


# base for collecting fields ,call init function
class ModelTypeBase(type):
    models = {}
    locker = None

    @property
    def fields(self):
        return self._fields

    @property
    def scripts(self):
        return self._scripts

    @property
    def db_field(self):
        return self._db_field

    @property
    def expire_field(self):
        return self._expire_field

    def __new__(mcs, name, bases, d):
        instance = type.__new__(mcs, name, bases, d)
        instance._fields = []
        instance._scripts = []
        instance._db_field = None
        instance._expire_field = None

        for v in d.itervalues():
            if isinstance(v, ModelField):
                instance._fields.append(v)
            if isinstance(v, redisx.DbScript):
                instance._scripts.append(v)
        # print 'creating model {}'.format(name)
        if name not in (
                'ModelPb',
                'ModelPbHash',
                'ModelCounter',
                'ModelList',
                'ModelSet',
                'ModelMap',
                'ModelSimple',
                'ModelZSet'):
            if name != 'DynamicModelClass':
                assert (name not in ModelTypeBase.models)
            ModelTypeBase.models[name] = instance
        return instance

    @classmethod
    def init_model_types(mcs, setting, db_dict):
        # locker_db_name = getattr(setting, "LOCKER_DB_NAME", "cache_locker")
        # locker_db = db_dict.get(locker_db_name)
        # if not locker_db:
        #     print "locker_db_name:{} is not found".format(locker_db_name)
        #     assert locker_db
        #
        # mcs.locker = redisx.Locker(setting, locker_db)
        # redisx.init_scripts(redisx.Locker, locker_db)
        for cls_model in mcs.models.itervalues():
            cls_model.init(setting, db_dict)
            cls_model.init_late(setting)
        for cls_model in mcs.models.itervalues():
            cls_model.on_init(setting)

    # @classmethod
    # def add_script(mcs, reg_obj):
    #     print 'add script {}'.format(reg_obj)
    #     mcs.scripts.append(reg_obj)

    def init(self, setting, db_dict):
        for f in self.fields:
            ft = type(f)
            setattr(self, ft.FUNCTION_KEY, f)

        print "[model]init db config", self
        assert (self.db_field and 'model must set db field')
        # this allowed default db
        # if not self.db_field:
        #     self.db_field = DbField('default')

        self.db = db_dict.get(self.db_field.name)
        assert (self.db and 'db must in config')
        # this allowed default db
        # if not self.db:
        #     self.db = dbdict.get('default')

        self.locker = ModelTypeBase.locker
        for f in self.fields:
            f.init(self)

        for s in self.scripts:
            s.init(self.db)

        print '[model]type={} db={} base={}'.format(self, self.db.name, self.__base__.__name__)


def create_metaclass(meta, *bases):
    """Create a base class with a metaclass."""

    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class Metaclass(meta):
        # def __new__(cls, name, this_bases, d):
        def __new__(cls, name=None, this_bases=None, d=None):
            return meta(name, bases, d)

    return type.__new__(Metaclass, 'temporary_class', (), {})


class ModelBaseObj(object):
    @classmethod
    def init_late(cls, setting):
        pass

    # when on init ,field db is all ready
    @classmethod
    def on_init(cls, setting):
        pass

    @classmethod
    def exist(cls, key):
        real_key = cls.key_field.build_real_key(key)
        return cls.db.exist(real_key)

    @property
    def df(self):
        return type(self).data_field

    @property
    def kf(self):
        return type(self).key_field

    @property
    def ef(self):
        return type(self).expire_field

    @property
    def db(self):
        return type(self).db

    @classmethod
    def delete_by_key(cls, key):
        real_key = cls.key_field.build_real_key(key)
        return cls.db.delete(real_key)

    @classmethod
    def exist(cls, key):
        real_key = cls.key_field.build_real_key(key)
        return cls.db.exist(real_key)

    @classmethod
    def expire(cls, key, exp):
        real_key = cls.key_field.build_real_key(key)
        return cls.db.expire(real_key, exp)

    @classmethod
    def expire_by_key(cls, key, exp):
        real_key = cls.key_field.build_real_key(key)
        return cls.db.expire(real_key, exp)
