# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj


class ModelList(create_metaclass(ModelTypeBase, ModelBaseObj)):
    @classmethod
    def get(cls, key):
        kf = cls.key_field
        realkey = kf.build_real_key(key)
        m = cls()
        m.real_key = realkey
        m.key = key
        return m

    def length(self):
        return self.db.llen(self.real_key)

    def get_by_index(self, index):
        return self.df.from_string(self.db.lindex(self.real_key, index))

    def push_back(self, *data, **kwargs):
        if data:
            save_str = [self.df.to_string(d) for d in data]
            cur_len = self.db.rpush(self.real_key, *save_str)
            max_len = kwargs.get('max', None)
            if max_len:
                pop = []
                while cur_len > max_len:
                    pop.append(self.pop_front())
                    cur_len = self.length()
                return pop
            return None

    def pop_front(self):
        data_str = self.db.lpop(self.real_key)
        return self.df.from_string(data_str)

    def push_front(self, *data, **kwargs):
        if data:
            save_str = [self.df.to_string(d) for d in data]
            cur_len = self.db.lpush(self.real_key, *save_str)
            max_len = kwargs.get('max', None)
            if max_len:
                pop = []
                while cur_len > max_len:
                    pop.append(self.pop_back())
                    cur_len = self.length()
                return pop
            return None

    def pop_back(self):
        data_str = self.db.rpop(self.real_key)
        return self.df.from_string(data_str)

    def get_range(self, start, end):
        return map(self.df.from_string, self.db.lrange(self.real_key, start, end))

    def get_all(self):
        return self.get_range(0, -1)

    def trim(self, start, end):
        return self.db.ltrim(self.real_key, start, end)

    def delete(self):
        return type(self).delete_by_key(self.key)

    def set_expire(self, second):
        return self.db.expire(self.real_key, second)

    def rem(self, count, value):
        pass

    def get_value(self, index, default=None):
        ret = self.db.lindex(self.real_key, index)
        if ret is None:
            return default
        df = self.data_field
        return df.from_string(ret)

    def __getitem__(self, index):
        return self.get_value(index)
