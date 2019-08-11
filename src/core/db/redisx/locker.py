# -*- coding:utf-8 -*-

import sys
import os
import dbscript
from contextlib import contextmanager
from collections import defaultdict
import gevent
import gevent.local

local_data = gevent.local.local()


class LockException(Exception):
    pass


def get_co_id():
    return id(gevent.getcurrent())


def debug_request():
    # from flask import request
    # if request:
    #     return '[{}]({}),path={}'.format(request.method,request.player_id,request.path)
    # else:
    #     return ''
    return ''


class Locker(object):
    __lock_counter = 0

    unlock_script = dbscript.reg_lua_script('''
        local uidlock = ARGV[1]
        local k = KEYS[1]
        local v = redis.pcall('get',k)
        local ret = nil
        if v == uidlock then
            ret = redis.pcall('del',k)
        end
        return ret
    ''')

    def __init__(self, setting, db, **kwargs):
        self._expire_time = setting.locker_expired
        self.db = db
        self.debug = setting.debug_lock
        self.max_retry = setting.MAX_RETRY
        self.log = kwargs.get("log", None)
        self.lock_exception_cls = kwargs.get("lock_exception", None)
        if not self.lock_exception_cls:
            self.lock_exception_cls = LockException

    def build_key(self, key):
        if not key:
            debug_str = 'try lock empty key in request {}'.format(debug_request())
            raise self.lock_exception_cls(debug_str)
        return "lock:{}".format(key)

    def del_lock(self, key, uid_lock):
        return self.unlock_script.call((key,), (uid_lock,))

    @contextmanager
    def lock(self, *keys):
        r_keys = [self.build_key(k) for k in keys]
        # use uid_lock avoid remove other process's key after expired
        # print 'dist_lock',uid_lock

        if not hasattr(local_data, 'co_id'):
            local_data.co_id = get_co_id()
            local_data.locked = defaultdict(int)
            # print '[lock]create co',local_data.co_id

        if self.debug:
            currentframe = sys._getframe(2)
            line_no = currentframe.f_lineno
            file_name = os.path.splitext(os.path.basename(currentframe.f_code.co_filename))[0]
            uid_lock = '{},{}:{}'.format(local_data.co_id, file_name, line_no)
        else:
            uid_lock = str(self.__lock_counter)
            self.__lock_counter += 1

        try:
            # print "getting lock:",rkeys
            t = self._acquire_lock(local_data, uid_lock, r_keys)
            yield t
        finally:
            self._release_lock(local_data, uid_lock, r_keys)
            # print "unlocked:",rkeys

    dist_lock = lock

    def _acquire_lock(self, data_local, uid_lock, r_keys):
        lock_dict = data_local.locked
        wait = 0.1
        retry = 0
        for r_key in r_keys:
            while retry < self.max_retry:
                if lock_dict[r_key] == 0:
                    # lock key will expire after expire times
                    if self.db.set(r_key, uid_lock, ex=self._expire_time, nx=True):
                        # print '[lock]co {} lock {} {}'.format(local_data.co_id,rkey,uidlock)
                        lock_dict[r_key] += 1
                        break
                    else:
                        retry += 1
                        lock_str = self.db.get(r_key)if self.debug and retry > 0 else ''
                        if self.log:
                            self.log.info(
                                '[lock]co {} waiting for {} of {},retry={},lock={},req={}'.format(
                                    data_local.co_id, r_key, r_keys, retry, lock_str, uid_lock))
                        gevent.sleep(wait * retry)
                else:
                    # print 'lock {} depth {}'.format(rkey,lock_dict[rkey])
                    lock_dict[r_key] += 1
                    break
        if retry >= self.max_retry:
            raise self.lock_exception_cls('retry too much')

        # print '[lock]acquire',local_data.co_id,lock_dict,rkeys,id(lock_dict)
        return True

    def _release_lock(self, data_local, uid_lock, r_keys):
        r_keys.reverse()
        lock_dict = data_local.locked
        for r_key in r_keys:
            lock_dict[r_key] -= 1
            if lock_dict[r_key] == 0:
                # print '[lock]co {} unlock {}'.format(local_data.co_id,rkey)
                self.del_lock(r_key, uid_lock)
            # else:
            # print 'unlock {} depth {}'.format(rkey,lock_dict[rkey])
        # print '[lock]release',local_data.co_id,lock_dict
