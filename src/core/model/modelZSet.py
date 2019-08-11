# -*- coding:utf-8 -*-

import random
from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj


class ModelZSet(create_metaclass(ModelTypeBase, ModelBaseObj)):
    @classmethod
    def get(cls, key):
        kf = cls.key_field
        real_key = kf.build_real_key(key)
        m = cls()
        m.exist = True
        m.real_key = real_key
        m.key = key
        return m

    def length(self):
        return self.db.zcard(self.real_key)

    def add(self, *data, **kwargs):
        data_len = len(data)
        save_str = []

        for i in xrange(0, data_len, 2):
            if i >= data_len or i + 1 >= data_len:
                break
            score = data[i]
            d = data[i + 1]
            if type(score) != int and type(score) != float:
                continue
            save_str.append(float(score))
            save_str.append(self.df.to_string(d))

        if save_str:
            self.db.zadd(self.real_key, *save_str)
            max_len = kwargs.get('max', None)
            if max_len:
                cur_len = self.length()
                while cur_len > max_len:
                    self.remove_by_index(0, 0)
                    cur_len = self.length()

    def remove(self, *data):
        del_str = [self.df.to_string(d) for d in data]
        return self.db.zrem(self.real_key, *del_str)

    def remove_by_rank(self, start, end):
        return self.db.zremrangebyrank(self.real_key, start, end)

    def remove_by_index(self, start, end):
        return self.db.zremrangebyrank(self.real_key, start, end)

    def remove_by_score(self, score):
        return self.db.zremrangebyscore(self.real_key, float(score), float(score))

    def remove_by_score_range(self, s, e):
        return self.db.zremrangebyscore(self.real_key, float(s), float(e))

    def count_by_score(self, score):
        return self.db.zcount(self.real_key, float(score), float(score))

    def contains(self, data):
        return self.get_score(data)

    def get_score(self, data):
        return self.db.zscore(self.real_key, self.df.to_string(data))

    def get_rank(self, data):
        return self.db.zrevrank(self.real_key, self.df.to_string(data))

    def get_all(self):
        return map(self.df.from_string, self.db.zrange(self.real_key, 0, -1))

    def get_range_by_score(self, score, offset=None, limit=None):
        return map(self.df.from_string, self.db.zrangebyscore(self.real_key, float(score), float(score), offset, limit))

    def get_range_by_rank(self, start, end, withscores=False):
        return map(self.df.from_string, self.db.zrange(self.real_key, start, end, withscores))

    def get_range_by_score_range(self, s, e, offset=None, limit=None, withscores=False):
        l_range = self.db.zrangebyscore(self.real_key, float(s), float(e), offset, limit, withscores)
        return map(self.df.from_string, l_range)

    def remove_by_range(self, start, end):
        return self.db.zremrangebyrank(self.real_key, start, end)

    def delete(self):
        return type(self).delete_by_key(self.key)

    def random(self):
        length = self.length()
        if length > 0:
            index = random.randint(0, length - 1)
            return self.df.from_string(self.db.zrange(self.real_key, index, index))
