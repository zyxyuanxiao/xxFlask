# -*- coding:utf-8 -*-
import sys
import time
import redis
import rediscluster
import cachetools
import gevent
import traceback


# import actkit.misckit as misckit


class RedisNotReady(Exception):
    pass


class RedisCommandCheckError(Exception):
    pass


DB_RECONNECT_DELAY = 5
MAX_ACCESS_COUNT_SECONDS_RECORD = 3600
MAX_ACCESS_LIMIT = 10000
MAX_QUEUE_SIZE = 1000


def current_db():
    return RedisDB.DB_DICT


def create_db(setting, log_helper=None):
    RedisDB.DB_DICT = {r['NAME']: RedisDB(r, setting.DB_CHECK, log_helper) for r in setting.REDIS}
    return RedisDB.DB_DICT


def db_by_name(name):
    return RedisDB.DB_DICT.get(name)


def all_running():
    def is_all_running():
        for v in RedisDB.DB_DICT.itervalues():
            if not v.running:
                print '[db]db {} is not running!!!'.format(v.name)
                return False
        RedisDB.all_running = True
        return True

    return RedisDB.all_running or is_all_running()


class RedisDB(object):
    default = None
    DB_DICT = {}
    all_running = True

    def __init__(self, config, db_check, log_helper=None):
        self.log = log_helper
        self.config = config
        self.name = config['NAME']
        self.is_cluster = config['IS_CLUSTER']
        if self.name == 'default':
            RedisDB.default = self
        self.logging = config.get('LOG', False)
        self.access_count = cachetools.LRUCache(maxsize=MAX_ACCESS_COUNT_SECONDS_RECORD)
        self.access_count_max = 1000
        self.pool = None
        self.redis = None
        self.create_time = 0
        self.reconnecting = False
        self.db_check_cmd(db_check)

        # self.set('test', '1')
        # self.get('test')
        # self.delete('test')

    def info(self, msg):
        if not self.log:
            return
        self.log.info(msg, "", 0, 4)

    def err(self, msg):
        if not self.log:
            return
        self.log.err(msg, "", 0, 4)

    @staticmethod
    def trace_full(frame_level=2):
        exc_info = sys.exc_info()
        stack = traceback.extract_stack()
        tb = traceback.extract_tb(exc_info[frame_level])
        full_tb = stack[:-1] + tb
        exc_line = traceback.format_exception_only(*exc_info[:frame_level])
        return "Traceback (most recent call last):\n{}\n{}".format(
            "".join(traceback.format_list(full_tb)),
            "".join(exc_line))

    def db_status(self):
        ret = dict()
        ret['name'] = self.name
        ret['access_count_max'] = self.access_count_max
        ret['access_count'] = {k: v for k, v in self.access_count.iteritems()}
        return ret

    def db_desc(self):
        if self.is_cluster:
            return "[{},CLUSTER]".format(self.name)
        else:
            return "[{},{}:{}]".format(self.name, self.config["HOST"], self.config["PORT"])

    def db_check_cmd(self, db_check):
        if db_check:
            with open('./common/redis/dbcheck.lua', 'r') as script_file:
                script = script_file.read()
                self.script_check(None, script, 0)

    @property
    def running(self):
        return self.redis

    def on_except(self):
        if self.pool:
            self.pool.disconnect()
            self.pool = None
        self.redis = None
        self.reconnecting = False
        RedisDB.all_running = False

    def db_check(self, func):
        def decorate(*args, **kwargs):
            while True:
                try:
                    if not self.redis:
                        raise RedisNotReady('[db]connection {} is not ready!!!'.format(self.db_desc()))

                    ret = func(*args, **kwargs)
                    now_sec = int(time.time())
                    next_cnt = self.access_count.get(now_sec, 0) + 1
                    self.access_count[now_sec] = next_cnt
                    if next_cnt > self.access_count_max:
                        self.access_count_max = next_cnt
                        self.info('[db]connection {} access max={}'.format(self.db_desc(), next_cnt))
                    if next_cnt >= MAX_ACCESS_LIMIT:
                        self.err('[db]connection {} access too fast... wait'.format(self.db_desc()))
                        gevent.sleep(now_sec + 1 - time.time())
                    return ret
                except RedisCommandCheckError as e:
                    raise e
                except redis.exceptions.NoScriptError as e:
                    raise e
                except RedisNotReady as e:
                    self.on_except()
                    self.info("{}".format(e))
                    self.connect()
                except Exception as e:
                    self.on_except()
                    self.err(self.trace_full())
                    self.err('[db]exception={} args={}'.format(e, args))
                    self.connect()

        return decorate

    def connect(self):
        config = self.config
        while self.redis is None:
            while self.reconnecting:
                self.info('[db]reconnecting to {} is still in process, just wait.'.format(self.db_desc()))
                gevent.sleep(DB_RECONNECT_DELAY)

            if self.redis:
                return

            try:
                self.reconnecting = True
                while True:
                    dif = abs(time.time() - self.create_time)
                    if dif >= DB_RECONNECT_DELAY:
                        break

                    wait = DB_RECONNECT_DELAY - dif
                    self.info('[db]reconnect to {} need wait {} seconds'.format(self.db_desc(), wait))
                    gevent.sleep(wait)

                self.create_time = time.time()
                self.info('[db]connecting to {}.'.format(self.db_desc()))
                if self.is_cluster:
                    nodes = config['REDIS_NODES']
                    n_redis = rediscluster.StrictRedisCluster(startup_nodes=nodes,
                                                              max_connections=2 ** 31,
                                                              socket_keepalive=True)
                else:
                    self.pool = redis.ConnectionPool(host=config['HOST'],
                                                     port=config['PORT'],
                                                     password=config['PASSWORD'],
                                                     db=0, socket_keepalive=True)
                    n_redis = redis.StrictRedis(connection_pool=self.pool)

                key = 'redis_db_test_key'
                n_redis.set(key, self.create_time)
                v = n_redis.get('redis_db_test_key')
                if not v:
                    raise Exception("test db error")

                self.redis = n_redis
                self.reconnecting = False
                self.info('[db]connect to {} success'.format(self.db_desc()))
            except Exception as e:
                self.err('[db]connect to {} exception={}'.format(self.db_desc(), e))
                self.on_except()

    # //////////////////////////////////////////////////////////////////////////////////////////////
    # //////////////////////////       redis string & key operation       //////////////////////////
    # //////////////////////////////////////////////////////////////////////////////////////////////

    @db_check
    def get(self, k):
        if self.logging:
            self.info("[db_get]key={}".format(k))
        return self.redis.get(k)

    @db_check
    def set(self, k, v, ex=None, px=None, nx=False, xx=False):
        if self.logging:
            self.info("[db_set]key={},len={}".format(k, len(str(v))))
        return self.redis.set(k, v, ex, px, nx, xx)

    def try_set(self, k, v, ex=None, px=None, nx=False, xx=False):
        if self.logging:
            self.info("[db_set]key={},len={}".format(k, len(v)))
        try:
            return self.redis.set(k, v, ex, px, nx, xx)
        except Exception as e:
            self.info('[db_set]failed when set key={}, except={}'.format(k, e))

    # @db_check
    def expire(self, k, second):
        if self.logging:
            self.info("[db_expire]key={},seconds={}".format(k, second))
        try:
            return self.redis.expire(k, second)
        except Exception as e:
            self.info('[db_expire]failed when save key={}, except={}'.format(k, e))

    @db_check
    def delete(self, *k):
        if self.logging:
            self.info("[db_del]key={}".format(k))
        return self.redis.delete(*k)

    @db_check
    def incr(self, k):
        if self.logging:
            self.info("[db_incr]key={}".format(k))
        return self.redis.incr(k)

    @db_check
    def decr(self, k):
        if self.logging:
            self.info("[db_decr]key={}".format(k))
        return self.redis.decr(k)

    @db_check
    def keys(self, pattern):
        raise Exception('fuck!!!! Do not use this !!!')

    @db_check
    def exist(self, k):
        if self.logging:
            self.info("[db_exists]k={}".format(k))
        return self.redis.exists(k)

    # //////////////////////////////////////////////////////////////////////////////////////////////
    # ///////////////////////           redis hash operation           /////////////////////////////
    # //////////////////////////////////////////////////////////////////////////////////////////////
    @db_check
    def hget(self, k, f):
        if self.logging:
            self.info("[db_hget]key={},field={}".format(k, f))
        return self.redis.hget(k, f)

    @db_check
    def hmget(self, k, *f):
        if self.logging:
            self.info("[db_hget]key={},field={}".format(k, f))
        return self.redis.hmget(k, *f)

    @db_check
    def hlen(self, k):
        if self.logging:
            self.info("[db_hlen]key={}".format(k))
        return self.redis.hlen(k)

    @db_check
    def hset(self, k, f, v):
        if self.logging:
            self.info("[db_hset]key={},field={},len={}".format(k, f, len(v)))
        return self.redis.hset(k, f, v)

    @db_check
    def hmset(self, k, mapping):
        if self.logging:
            self.info("[db_hmset]key={},fields={}".format(k, mapping.keys()))
        return self.redis.hmset(k, mapping)

    def try_hmset(self, k, mapping):
        try:
            return self.redis.hmset(k, mapping)
        except Exception as e:
            self.info('[db_try_hmset]faile when save key={}, except={}'.format(k, e))

    @db_check
    def hexists(self, k, f):
        if self.logging:
            self.info("[db_hexists]key={},field={}".format(k, f))
        return self.redis.hexists(k, f)

    @db_check
    def hgetall(self, k):
        if self.logging:
            self.info("[db_hgetall]key={}".format(k))
        return self.redis.hgetall(k)

    @db_check
    def hdel(self, k, *f):
        if self.logging:
            self.info("[db_hdel]key={},field={}".format(k, f))
        return self.redis.hdel(k, *f)

    @db_check
    def hkeys(self, k):
        if self.logging:
            self.info("[db_hkeys]key={}".format(k))
        return self.redis.hkeys(k)

    @db_check
    def hincrby(self, k, f, v=1):
        if self.logging:
            self.info("[db_hincrby]key={},field={},value={}".format(k, f, v))
        return self.redis.hincrby(k, f, v)

    # //////////////////////////////////////////////////////////////////////////////////////////////
    # ///////////////////////           redis list operation           /////////////////////////////
    # //////////////////////////////////////////////////////////////////////////////////////////////

    @db_check
    def ltrim(self, k, start, stop):
        if self.logging:
            self.info("[db_ltrim]key={},start={},stop={}".format(k, start, stop))
        return self.redis.ltrim(k, start, stop)

    @db_check
    def lindex(self, k, index):
        if self.logging:
            self.info("[db_lindex]key={},index={}".format(k, index))
        return self.redis.lindex(k, index)

    @db_check
    def lpop(self, k):
        if self.logging:
            self.info("[db_lpop]key={}".format(k))
        return self.redis.lpop(k)

    @db_check
    def rpop(self, k):
        if self.logging:
            self.info("[db_rpop]key={}".format(k))
        return self.redis.rpop(k)

    @db_check
    def rpush(self, k, *v):
        if self.logging:
            self.info("[db_rpush]key={},data_len={}".format(k, len(v)))
        if v:
            return self.redis.rpush(k, *v)

    @db_check
    def lpush(self, k, *v):
        if self.logging:
            self.info("[db_lpush]key={},data_len={}".format(k, len(v)))
        if v:
            return self.redis.lpush(k, *v)

    @db_check
    def lrange(self, k, start, stop):
        if self.logging:
            self.info("[db_lrange]key={},start={},stop={}".format(k, start, stop))
        return self.redis.lrange(k, start, stop)

    @db_check
    def llen(self, k):
        if self.logging:
            self.info("[db_llen]key={}".format(k))
        return self.redis.llen(k)

    # //////////////////////////////////////////////////////////////////////////////////////////////
    # ///////////////////////           redis zset operation           /////////////////////////////
    # //////////////////////////////////////////////////////////////////////////////////////////////

    @db_check
    def zadd(self, k, *data):
        if self.logging:
            self.info("[db_zadd]key={},data".format(k, data))
        return self.redis.zadd(k, *data)

    @db_check
    def zscore(self, k, member):
        if self.logging:
            self.info("[zscore]key={},member={}".format(k, member))
        return self.redis.zscore(k, member)

    @db_check
    def zrange(self, k, start, stop, withscores=False):
        if self.logging:
            self.info("[db_zrange]key={},star={},stop={}".format(k, start, stop))
        return self.redis.zrange(k, start, stop, withscores=withscores)

    @db_check
    def zrem(self, k, *member):
        if self.logging:
            self.info("[db_zrem]key={},member={}".format(k, member))
        return self.redis.zrem(k, *member)

    @db_check
    def zrangebyscore(self, k, start, stop, offset=None, limit=None, withscores=False):
        if self.logging:
            self.info("[zrangebyscore]key={},start={},stop={}".format(k, start, stop))
        return self.redis.zrangebyscore(k, start, stop, start=offset, num=limit, withscores=withscores)

    @db_check
    def zcard(self, k):
        if self.logging:
            self.info("[db_zcard]key={}".format(k))
        return self.redis.zcard(k)

    @db_check
    def zremrangebyrank(self, k, start, stop):
        if self.logging:
            self.info("[db_zremrangebyrank]key={},star={},stop={}".format(k, start, stop))
        return self.redis.zremrangebyrank(k, start, stop)

    @db_check
    def zremrangebyscore(self, k, start, stop):
        if self.logging:
            self.info("[zremrangebyscore]key={},star={},stop={}".format(k, start, stop))
        return self.redis.zremrangebyscore(k, start, stop)

    @db_check
    def zcount(self, k, start, stop):
        if self.logging:
            self.info("[zcount]key={},star={},stop={}".format(k, start, stop))
        return self.redis.zcount(k, start, stop)

    @db_check
    def zrank(self, k, member):
        if self.logging:
            self.info("[db_zrank]key={},member={}".format(k, member))
        return self.redis.zrank(k, member)

    @db_check
    def zrevrank(self, k, member):
        if self.logging:
            self.info("[db_zrevrank]key={},member={}".format(k, member))
        return self.redis.zrevrank(k, member)

    @db_check
    def zrevrange(self, k, start, stop, withscores=False,
                  score_cast_func=float):
        if self.logging:
            self.info("[zrevrange]key={},star={},stop={}".format(k, start, stop))
        return self.redis.zrevrange(k, start, stop, withscores, score_cast_func)

    # //////////////////////////////////////////////////////////////////////////////////////////////
    # ///////////////////////           redis set operation           /////////////////////////////
    # //////////////////////////////////////////////////////////////////////////////////////////////

    @db_check
    def sadd(self, k, *member):
        if self.logging:
            self.info("[db_sadd]key={},member={}".format(k, member))
        return self.redis.sadd(k, *member)

    @db_check
    def srem(self, k, *member):
        if self.logging:
            self.info("[db_srem]key={},member={}".format(k, member))
        return self.redis.srem(k, *member)

    @db_check
    def scard(self, k):
        if self.logging:
            self.info("[db_scard]key={}".format(k))
        return self.redis.scard(k)

    @db_check
    def smove(self, src, dst, member):
        if self.logging:
            self.info("[db_smove]src={},dst={},member={}".format(src, dst, member))
        return self.redis.smove(src, dst, member)

    @db_check
    def srandmember(self, k, count=None):
        if self.logging:
            self.info("[db_srandmember]key={},count={}".format(k, count))
        return self.redis.srandmember(k, count)

    @db_check
    def smembers(self, k):
        if self.logging:
            self.info("[db_smembers]key={}".format(k))
        return self.redis.smembers(k)

    @db_check
    def sismember(self, k, member):
        if self.logging:
            self.info("[db_sismember]key={},member={}".format(k, member))
        ret = self.redis.sismember(k, member)
        if ret == 1:
            return True
        else:
            return False

    @db_check
    def sinter(self, k, *args):
        if self.logging:
            self.info("[db_sinter]key={},args={}".format(k, args))
        return self.redis.sinter(k, *args)

    @db_check
    def sunion(self, k, *args):
        if self.logging:
            self.info("[db_sunion]key={},args={}".format(k, args))
        return self.redis.sunion(k, *args)

    @db_check
    def sdiff(self, k, *args):
        if self.logging:
            self.info("[db_sdiff]key={},args={}".format(k, args))
        return self.redis.sdiff(k, *args)

    @db_check
    def script(self, sha1, script, *args):
        if self.logging:
            self.info("[db_evalsha]script={}".format(sha1))
        try:
            if sha1:
                return self.redis.evalsha(sha1, *args)
            else:
                return self.redis.eval(script, *args)
        except redis.exceptions.NoScriptError:
            if self.logging:
                self.info("[db_eval]script={}".format(sha1))
            return self.redis.eval(script, *args)
        except Exception as e:
            self.err(self.trace_full())
            self.err('[db_eval]do script error!{} except={}'.format(args, e))
            return None

    @db_check
    def script_check(self, sha1, script, *args):
        if self.logging:
            self.info("[db_evalsha]script={}".format(sha1))
        try:
            if sha1:
                return self.redis.evalsha(sha1, *args)
            else:
                return self.redis.eval(script, *args)
        except redis.exceptions.ResponseError as e:
            raise RedisCommandCheckError("[db] unkonwn command execed , detail is {}".format(e.message))
        except Exception as e:
            self.err(self.trace_full())
            self.err('[db_eval]do script error!{} except={}'.format(args, e))
            return None
