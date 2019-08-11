from collections import defaultdict
from src.core.utils import zip_data
from src.core.utils.pb_tools import message_serialize_dict


class ModelPbBase(object):

    def __init__(self):
        self._obj = None

    def __repr__(self):
        return str(self.pbobj)

    @property
    def lockstr(self):
        return self.real_key

    @property
    def pbobj(self):
        return self._obj

    @classmethod
    def delete_by_key(cls, key):
        real_key = cls.build_real_key(key)
        return cls.db.delete(real_key)

    @classmethod
    def exist(cls, key):
        real_key = cls.build_real_key(key)
        return cls.db.exist(real_key)

    @classmethod
    def expire_by_key(cls, key, exp):
        real_key = cls.build_real_key(key)
        return cls.db.expire(real_key, exp)


class ModelPbHashBase(object):
    PacksDict = defaultdict(dict)

    DefaultField = ''

    @classmethod
    def delete_by_key(cls, key):
        real_key = cls.build_real_key(key)
        return cls.db.delete(real_key)

    @classmethod
    def exist(cls, key):
        real_key = cls.build_real_key(key)
        return cls.db.exist(real_key)

    @classmethod
    def expire_by_key(cls, key, exp):
        real_key = cls.build_real_key(key)
        return cls.db.expire(real_key, exp)

    @classmethod
    def packed_fields(cls, pack_name):
        if pack_name:
            return cls.PacksDict.get(pack_name, None)
        else:
            return cls.PacksDict['all']

    @classmethod
    def get_pack_data(cls, **kwargs):
        tmp_fields = kwargs.pop('fields', None)
        fd = cls.PacksDict['all']
        if tmp_fields:
            pack_data = {{n: fd[n] for n in tmp_fields}}
            if cls.DefaultField:
                pack_data[cls.DefaultField] = fd[cls.DefaultField]
        else:
            pack_data = fd
        return pack_data

    def __save_implement(self, fields, save_func):
        datas = message_serialize_dict(self._obj)
        if fields:
            fd = type(self).PacksDict['all']
            save_fields = (fd[n] for n in fields)
        else:
            save_fields = self._pack.itervalues()

        pbobj = self._obj
        save_dict = {}
        selfCls = type(self)
        for f in save_fields:
            d = datas.get(f.number, '')
            save_dict[f.name] = zip_data(d)

        rk = self.real_key
        save_func(rk, save_dict)
        ef = self.get_expire
        if ef:
            self.db.expire(rk, ef)

    def save(self, fields=None):
        return self.__save_implement(fields, type(self).db.hmset)

    def try_save(self, fields=None):
        return self.__save_implement(fields, type(self).db.try_hmset)

    def field_in_pack(self, fname):
        return fname in self._pack or fname == type(self).DefaultField

    @property
    def pbobj(self):
        return self._obj

    @property
    def lockstr(self):
        return self.real_key
