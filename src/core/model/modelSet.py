# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj


class ModelSet(create_metaclass(ModelTypeBase, ModelBaseObj)):
    @classmethod
    def get(cls, key):
        kf = cls.key_field
        realkey = kf.build_real_key(key)
        m = cls()
        m.exist = True
        m.real_key = realkey
        m.key = key
        return m

    def length(self):
        return self.db.scard(self.real_key)

    def add(self, *data):
        save_str = (self.df.to_string(d) for d in data)
        return self.db.sadd(self.real_key, *save_str)

    def remove(self, *data):
        del_str = (self.df.to_string(d) for d in data)
        return self.db.srem(self.real_key, *del_str)

    def contains(self, data):
        return self.db.sismember(self.real_key, self.df.to_string(data))

    def get_all(self):
        return map(self.df.from_string, self.db.smembers(self.real_key))

    def delete(self):
        return type(self).delete_by_key(self.key)

    def random_multi(self, count=1):
        rand_result = self.db.srandmember(self.real_key, count)
        return [self.df.from_string(r) for r in rand_result]

    # def pop(self,count=1):
    #    rand_result = self.db.spop(self.real_key,count)
    #    return [ self.df.from_string(r) for r in rand_result ]

    def random(self):
        rand_result = self.db.srandmember(self.real_key, 1)
        return self.df.from_string(rand_result)
