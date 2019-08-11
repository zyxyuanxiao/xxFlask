# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj
from src.core.model.modelFields import CounterField, DbField


class ModelTypeCounterBase(ModelTypeBase):
    @property
    def key(cls):
        return cls.counter_field.name

    @property
    def current(cls):
        r = cls.db.get(cls.key)
        return r and long(r)

    @property
    def next(cls):
        r = cls.db.incr(cls.key)
        return r and long(r)

    @property
    def prev(cls):
        r = cls.db.decr(cls.key)
        return r and long(r)


class ModelCounter(create_metaclass(ModelTypeCounterBase, ModelBaseObj)):
    dynamic_counters = {}

    @classmethod
    def on_init(cls, setting):
        if cls == ModelCounter:
            return

        cur_count = cls.current
        if cur_count:
            print '[counter]exist {}={}'.format(cls.key, cur_count)
        else:
            init_count = cls.counter_field.init_count
            print '[counter]init {}={}'.format(cls.key, init_count)
            cls.db.set(cls.key, init_count)

    @classmethod
    def create_dynamic(cls, name, init_counter, db):
        print '[counter]create dynamic counter {}'.format(name)

        class DynamicModelClass(ModelCounter):
            __conter = CounterField(init_counter, name)
            __db = DbField(db.name)

        DynamicModelClass.init(None, {db.name: db})
        return DynamicModelClass

    @classmethod
    def get_dynamic(cls, name, init_counter, db=None):
        ret = ModelCounter.dynamic_counters.get(name)
        if not ret:
            ret = cls.create_dynamic(name, init_counter, db)
            ModelCounter.dynamic_counters[name] = ret
        return ret

    @classmethod
    def key_name(cls):
        return cls.counter_field.name

    @classmethod
    def set(cls, count):
        cls.db.set(cls.key, count)

