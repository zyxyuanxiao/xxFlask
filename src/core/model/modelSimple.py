# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj


class ModelSimple(create_metaclass(ModelTypeBase, ModelBaseObj)):
    def __init__(self, key=None, expire=None):
        self.key = key
        self.expire = expire

    @classmethod
    def get(cls, key):
        m = cls()
        m.key = key
        return m

    @property
    def data(self):
        v = self.db.get(self.__real_key)
        if v:
            return self.df.from_string(v)
        else:
            return None

    @data.setter
    def data(self, data):
        v = self.df.to_string(data)
        self.db.set(self.__real_key, v, ex=self.expire)

    @data.deleter
    def data(self):
        self.db.delete(self.__real_key)

    @property
    def key(self):
        return self.key

    @key.setter
    def key(self, key):
        self.__key = key
        self.__real_key = self.kf.build_real_key(key)

    def delete(self):
        return type(self).delete_by_key(self.__real_key)
