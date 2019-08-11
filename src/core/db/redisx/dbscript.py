# -*- coding:utf-8 -*-

import itertools
import inspect
from hashlib import sha1 as sha


class DbScript(object):
    def __init__(self, script, name):
        self.keys = []
        self.args = []
        self.name = name
        self.script = script
        sha_obj = sha(script)
        self.sha1 = sha_obj.hexdigest()
        self.db = None

    def init(self, db):
        self.db = db
        print '[script]{} {} =>[db]{}'.format(self.name, self.sha1, db.name)

    def __call__(self, *args):
        return self.call((), args)

    def call(self, keys=tuple(), args=tuple(), db=None):
        call_args = itertools.chain(self.keys, keys, self.args, args)
        key_len = len(keys) + len(self.keys)
        db = db or self.db
        return db.script(self.sha1, self.script, key_len, *call_args)

    def add_key(self, *keys):
        self.keys.extend(keys)
        return self

    def add_arg(self, *args):
        self.args.extend(args)
        return self


def init_scripts(obj, db):
    for d in obj.__dict__.itervalues():
        if isinstance(d, DbScript):
            d.init(db)


def reg_lua_script(script_str, name=''):
    if not name:
        f = inspect.currentframe().f_back
        fi = inspect.getframeinfo(f)
        name = "{}:{}".format(fi.filename, fi.lineno)
    return DbScript(script_str, name)
