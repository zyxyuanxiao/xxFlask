# -*- coding:utf-8 -*-

# stdlib
import time
import sys
import traceback
import random
import gzip
import pprint
import inspect
import functools
import cProfile
import socket
import struct
from cStringIO import StringIO
from contextlib import contextmanager
import lz4

from Crypto.Hash import HMAC, MD5

pp = pprint.PrettyPrinter(indent=4).pprint
pretty_print = pp


def typecheck(*ty_args, **ty_kwargs):
    def decorate(func):
        bound_types = inspect.getcallargs(func, *ty_args, **ty_kwargs)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound_values = inspect.getcallargs(func, *args, **kwargs)
            for name, value in bound_values.items():
                if name in bound_types:
                    if not isinstance(value, bound_types[name]):
                        raise TypeError('Argument {} must be {}'.format(name, bound_types[name]))
            return func(*args, **kwargs)

        return wrapper

    return decorate


def profile(name='func_profile'):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            prof = cProfile.Profile()
            retval = prof.runcall(func, *args, **kwargs)
            prof.dump_stats(name)
            return retval

        return wrapper

    return decorate


def trace_full(frame_level=2):
    exc_info = sys.exc_info()
    stack = traceback.extract_stack()
    tb = traceback.extract_tb(exc_info[frame_level])
    full_tb = stack[:-1] + tb
    exc_line = traceback.format_exception_only(*exc_info[:frame_level])
    return "Traceback (most recent call last):\n{}\n{}".format(
        "".join(traceback.format_list(full_tb)),
        "".join(exc_line)
    )


def pad(seq, target_length, padding=None):
    tobe_add = target_length - len(seq)
    if tobe_add > 0:
        seq.extend([padding] * tobe_add)


class RetryException(Exception):
    pass


class RetryTooMuchException(Exception):
    pass


def retry_func(max_retry=100, delay=0.01):
    def func_with_max_retry(func):
        @functools.wraps(func)
        def func_retry(*args, **kwargs):
            success = False
            ret = None
            for i in xrange(0, max_retry):
                try:
                    ret = func(*args, **kwargs)
                    success = True
                except RetryException as e:
                    success = False
                    # info('func {},retry {}'.format(func.__name__,i))
                    time.sleep(delay)
                if success:
                    break
            if success == False:
                # info('func {},retry too much'.format(func.__name__) )
                raise RetryTooMuchException()
            return ret

        return func_retry

    return func_with_max_retry


def ip_to_int(ip):
    return socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])


def remove_password(d):
    for k, v in d.iteritems():
        if isinstance(v, dict):
            remove_password(v)
        else:
            if str(k) in ('password', 'passwordHashed', 'transactionReceipt', 'ldap_password') >= 0:
                if len(d[k]) > 0:
                    d[k] = "*"


def random_password(length=6):
    # lib = string.digits[2:] + string.uppercase without I and O
    LETTERS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    return ''.join(random.sample(LETTERS, length))


def sign_string(signString, key, shaCls, pkcs):
    signer = pkcs.new(key)
    sha = shaCls.new(signString)
    return signer.sign(sha)


def verify_string(verifyString, sign, key, shaCls, pkcs):
    sha = shaCls.new(verifyString)
    signer = pkcs.new(key)
    return signer.verify(sha, sign)


def md5_digest_string(string):
    return MD5.new(string).hexdigest()


def hmac_digest_string(key, signString, digMod=None, isHex=True):
    h = HMAC.new(key, signString, digMod)
    return h.hexdigest() if isHex else h.digest()


def trans_wechat_dict_to_xml(data):
    xml = []
    for k in sorted(data.keys()):
        v = data[k]
        if k == 'detail' and not v.startswith('<![CDATA['):
            v = '<![CDATA[{}]]>'.format(v)
        xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(xml))


def ncycles(iterable, n):
    "Returns the sequence elements n times"
    for i in xrange(n):
        for it in iterable:
            yield it


def gzip_str(s):
    gzip_buffer = StringIO()
    with gzip.GzipFile(mode='wb', fileobj=gzip_buffer, compresslevel=4) as gf:
        gf.write(s)
    return gzip_buffer.getvalue()


def ungzip_str(buf):
    obj = StringIO(buf)
    with gzip.GzipFile(fileobj=obj) as f:
        result = f.read()
        return result
    return 0


def binary_search(l, val, cmp=None, key=None, start=None, end=None):
    head = start if start else 0
    tail = end if end else len(l) - 1

    if head < 0 or head >= len(l):
        return False, -1
    if tail < 0 or tail >= len(l):
        return False, -1
    if head > tail:
        return False, -1

    def val_cmp(a, b):
        if cmp:
            return cmp(a, b)
        elif key:
            k_a = key(a)
            k_b = key(b)
            return k_a - k_b
        else:
            return a - b

    while head <= tail:
        mid = (head + head) / 2
        if val_cmp(l[mid], val) > 0:
            tail = mid - 1
        elif val_cmp(l[mid], val) < 0:
            head = mid + 1
        else:
            return True, mid

    return False, head - 1


@contextmanager
def test_timer(name=''):
    try:
        start = time.time()
        yield
    finally:
        finish = time.time()
        cost = round((finish - start) * 1000, 3)
        print "[TimeCost]{} {}ms".format(name, cost)


debug_timer = test_timer


def func_timer(func):
    def decorator_func(*args, **kwargs):
        with test_timer(func):
            return func(*args, **kwargs)

    return decorator_func


def class_to_dict(cls):
    dic = {}
    if cls != object:
        for base in cls.__bases__:
            dic.update(class_to_dict(base))
    for k, v in cls.__dict__.iteritems():
        if not k.startswith('__') and not isinstance(v, classmethod):
            dic[k] = v
    return dic


def zip_data(data):
    try:
        return lz4.frame.compress(data, 0)
    except Exception as e:
        print "zip data {} failed".format(data)
        return data


def unzip_data(data):
    try:
        return lz4.frame.decompress(data)
    except Exception as e:
        print "unzip data {} failed".format(data)
        return data


def pbobj_from_string(data_cls):
    obj = data_cls()

    def wrapper(data_str):
        return obj.MergeFromString(data_str)

    return wrapper
