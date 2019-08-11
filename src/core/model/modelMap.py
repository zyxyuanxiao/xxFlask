# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj


class ModelMap(create_metaclass(ModelTypeBase, ModelBaseObj)):
    @classmethod
    def get(cls, key):
        kf = cls.key_field
        real_key = kf.build_real_key(key)
        m = cls()
        m.real_key = real_key
        m.key = key
        return m

    def length(self):
        return self.db.hlen(self.real_key)

    def get_value(self, k, default=None):
        ret = self.db.hget(self.real_key, k)
        if ret is None:
            return default
        df = self.data_field
        return df.from_string(ret)

    def get_muti(self, *keys):
        ret = self.db.hmget(self.real_key, *keys)
        if ret:
            df = self.data_field
            return {k: (df.from_string(ret[i]) if ret[i] is not None else None) for i, k in enumerate(keys)}
        else:
            return dict()

    def remove(self, *k):
        return self.db.hdel(self.real_key, *k)

    def contains(self, k):
        return self.db.hexists(self.real_key, k)

    def get_all(self):
        ret = self.db.hgetall(self.real_key)
        if ret:
            df = self.df
            return {k: df.from_string(v) for k, v in ret.iteritems()}
        else:
            return dict()

    def keys(self):
        ret = self.db.hkeys(self.real_key)
        return ret

    def clear(self):
        return self.db.delete(self.real_key)

    def set_multi(self, d):
        return self.db.hmset(self.real_key, d)

    def save_multi(self, mapping):
        d = {k: self.df.to_string(v) for k, v in mapping.iteritems()}
        return self.set_multi(d)

    def set_expire(self, second):
        return self.db.expire(self.real_key, second)

    def delete(self):
        return type(self).delete_by_key(self.key)

    def __len__(self):
        return self.db.hlen(self.real_key)

    def __getitem__(self, k):
        return self.get_value(k)

    def __setitem__(self, k, v):
        self.db.hset(self.real_key, k, self.df.to_string(v))

    def __delitem__(self, k):
        return self.remove(k)
