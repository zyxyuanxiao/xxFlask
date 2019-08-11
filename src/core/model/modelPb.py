# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import create_metaclass, ModelTypeBase, ModelBaseObj
from src.core.utils import pbx, pb_tools
from src.core.log import *

try:
    lz4 = __import__("lz4.frame")
except Exception as e:
    lz4 = None


class ModelPb(create_metaclass(ModelTypeBase, ModelBaseObj)):
    NeedZip = False

    def __str__(self):
        return str(self._obj)

    @classmethod
    def init_late(cls, setting):
        if cls == ModelPb:
            return

        def make_property(fname):
            def getter(self):
                return getattr(self._obj, fname)

            def setter(self, v):
                setattr(self._obj, fname, v)

            return property(getter, setter)

        fds = cls.data_field.fields_dict
        for k, f in fds.iteritems():
            if hasattr(cls, f.name):
                raise Exception('init field {} failed because exist'.format(f.name))
            setattr(cls, f.name, make_property(f.name))

    @classmethod
    def zip_data(cls, value):
        if not cls.NeedZip:
            return value

        if not lz4:
            return value

        # print 'lz4 {} {}={}'.format(cls.__name__,len(value),len(lz4.frame.compress(value,0)))
        return lz4.frame.compress(value, 0)

    @classmethod
    def unzip_data(cls, data):
        if not cls.NeedZip:
            return data

        if not lz4:
            return data

        try:
            return lz4.frame.decompress(data)
        except Exception as err:
            print "unzip field of {} failed:{}".format(cls.__name__, err)
            return data

    @classmethod
    def on_init(cls, setting):
        if cls == ModelPb:
            return

    @classmethod
    def get(cls, key, **kwargs):
        real_key = cls.key_field.build_real_key(key)
        data = cls.db.get(real_key)
        if data:
            pbobj = cls.data_field.from_string(cls.unzip_data(data))
            obj = cls(obj=pbobj)
            return obj
        return None

    @classmethod
    def get_create(cls, key, **kwargs):
        ret = cls.get(key, **kwargs)
        if not ret:
            ret = cls()
            if cls.key_field.pb_key:
                ret.set_key(key)
        return ret

    def __init__(self, **kwargs):
        self._obj = kwargs.pop('obj', None) or self.df.create_data()

    @property
    def pbobj(self):
        return self._obj

    def get_key(self):
        return self.kf.name and getattr(self, self.kf.name)

    def set_key(self, v):
        setattr(self, self.kf.name, v)

    @property
    def expire(self):
        return self.ef and getattr(self._obj, self.ef.name)

    @expire.setter
    def expire(self, v):
        setattr(self._obj, self.ef.name, v)

    @property
    def real_key(self):
        return self.kf.build_real_key(self.get_key())

    def copy_to(self, pbobj):
        return pbobj.CopyFrom(self._obj)

    def to_json(self):
        return pbx.json_format.MessageToJson(self._obj, True)

    def save(self):
        rk = self.real_key
        data = self.df.to_string(self._obj)
        ef = self.expire
        self.db.set(rk, type(self).zip_data(data), ef)

    def try_save(self):
        rk = self.real_key
        data = self.df.to_string(self._obj)
        ef = self.expire
        self.db.try_set(rk, type(self).zip_data(data), ef)

    def delete(self):
        return type(self).delete_by_key(self.get_key())


class ModelPbHash(ModelPb):
    Packs = {}
    DefaultField = None
    ZipField = None

    @classmethod
    def init_late(cls, setting):
        if cls == ModelPbHash:
            return

        if setting.DEBUG:
            def make_property(fname):
                def getter(self):
                    if not self.field_in_pack(fname):
                        raise Exception('access field {} must in pack'.format(fname))
                    return getattr(self._obj, fname)

                def setter(self, value):
                    if not self.field_in_pack(fname):
                        raise Exception('access field {} must in pack'.format(fname))
                    setattr(self._obj, fname, value)

                return property(getter, setter)
        else:
            def make_property(fname):
                def getter(self):
                    return getattr(self._obj, fname)

                def setter(self, value):
                    setattr(self._obj, fname, value)

                return property(getter, setter)

        fds = cls.data_field.fields_dict

        for k, f in fds.iteritems():
            if hasattr(cls, f.name):
                raise Exception('init field {} failed because exist'.format(f.name))
            setattr(cls, f.name, make_property(f.name))

        # print 'initLate',cls.__name__, cls.data_field.data_cls()
        setattr(cls, 'PacksDict', {})

        d = cls.data_field.fields_dict
        cls.PacksDict['all'] = d
        if cls.Packs:
            for k, v in cls.Packs.iteritems():
                cls.PacksDict[k] = {fname: d[fname] for fname in v}

        print '[packs]{} {}'.format(cls.__name__, cls.PacksDict)

    @classmethod
    def on_init(cls, setting):
        if cls in (ModelPb, ModelPbHash):
            return

    @classmethod
    def zip_field(cls, field, value):
        if not cls.ZipField or field not in cls.ZipField:
            return value

        if not lz4:
            return value

        # print 'lz4 {} {}={}'.format(field,len(value),len(lz4.frame.compress(value,0)))
        return lz4.frame.compress(value, 0)

    @classmethod
    def unzip_field(cls, field, data):
        if not cls.ZipField or field not in cls.ZipField:
            return data

        if not lz4:
            return data

        try:
            return lz4.frame.decompress(data)
        except Exception as err:
            print "unzip field error {}".format(field, err)
            return data

    @classmethod
    def packed_fields(cls, pack_name):
        if pack_name:
            return cls.Packs.get(pack_name, None)
        else:
            return cls.data_field.fields_name

    @classmethod
    def get_pack_data(cls, **kwargs):
        tmp_fields = kwargs.pop('fields', None)
        fd = cls.data_field.fields_dict
        if tmp_fields:
            pack_data = {n: fd[n] for n in tmp_fields}
            if cls.DefaultField:
                pack_data[cls.DefaultField] = fd[cls.DefaultField]
        else:
            pack_name = kwargs.pop('pack', 'all')
            pack_data = cls.PacksDict.get(pack_name)

        return pack_data

    @classmethod
    def get_create(cls, key, **kwargs):
        ret = cls.get(key, **kwargs)
        if not ret:
            ret = cls(None, cls.get_pack_data(**kwargs))
            if cls.key_field.pb_key:
                ret.set_key(key)
        return ret

    @classmethod
    def get_real_key(cls, key):
        return cls.key_field.build_real_key(key)

    @classmethod
    def check_datas(cls, datas):
        for data in datas:
            if data is not None:
                return True
        return False

    @classmethod
    def get(cls, key, **kwargs):
        fd = cls.data_field.fields_dict
        pack_data = cls.get_pack_data(**kwargs)
        real_key = cls.key_field.build_real_key(key)
        fieldkeys = pack_data.keys()
        datas = cls.db.hmget(real_key, *fieldkeys)
        if cls.check_datas(datas):
            pbobj = cls.data_field.create_data()
            for i, d in enumerate(datas):
                if d:
                    f = fd[fieldkeys[i]]
                    if pb_tools.is_scalar(f):
                        data = pb_tools.packed_to_scalar(f, d)
                        setattr(pbobj, f.name, data)
                    else:
                        data = cls.unzip_field(f.name, d)
                        ret = pbobj.MergeFromString(data)
                        if ret != len(data):
                            ERROR('decode {} {} something wrong!!!'.format(cls.__name__, f.name))
            obj = cls(pbobj, pack_data)
            if cls.key_field.pb_key:
                obj.set_key(key)
            return obj
        return None

    def load_more(self, fields):
        if not fields:
            return

        self_cls = type(self)
        fd = self_cls.data_field.fields_dict
        pack_data = {n: fd[n] for n in fields}
        field_keys = pack_data.keys()
        datas = self_cls.db.hmget(self.real_key, *field_keys)
        if self_cls.check_datas(datas):
            for i, d in enumerate(datas):
                if d:
                    f = fd[field_keys[i]]
                    if pb_tools.is_scalar(f):
                        data = pb_tools.packed_to_scalar(f, d)
                        setattr(self.pbobj, f.name, data)
                    else:
                        data = self_cls.unzip_field(f.name, d)
                        ret = self.pbobj.MergeFromString(data)
                        if ret != len(data):
                            ERROR('decode {} {} something wrong!!!'.format(self_cls.__name__, f.name))
                        else:
                            self._pack[field_keys[i]] = f

    def __save_implement(self, fields, save_func, keep_raw):
        datas = pb_tools.message_serialize_dict(self._obj)
        if fields:
            fd = self.df.fields_dict
            save_fields = (fd[n] for n in fields)
        else:
            save_fields = self._pack.itervalues()

        if keep_raw:
            self.raw_dict = {}

        pbobj = self._obj
        save_dict = {}
        self_cls = type(self)
        for f in save_fields:
            if pb_tools.is_scalar(f):
                v = getattr(pbobj, f.name)
                save_dict[f.name] = pb_tools.scalar_to_packed(f, v)
            else:
                d = datas.get(f.number, '')
                if keep_raw:
                    self.raw_dict[f.name] = d
                save_dict[f.name] = self_cls.zip_field(f.name, d)

        rk = self.real_key
        save_func(rk, save_dict)
        ef = self.expire
        if ef:
            self.db.expire(rk, ef)

    def save(self, fields=None, keep_raw=False):
        return self.__save_implement(fields, self.db.hmset, keep_raw)

    def try_save(self, fields=None, keep_raw=False):
        return self.__save_implement(fields, self.db.try_hmset, keep_raw)

    def __init__(self, pbobj=None, pack_data=None, fields=None, *args, **kwargs):
        super(ModelPbHash, self).__init__()
        self._obj = pbobj or self.df.create_data()
        if fields:
            d = self.df.fields_dict
            self._pack = {n: d[n] for n in fields}
        else:
            self._pack = pack_data or type(self).PacksDict.get('all')

    def field_in_pack(self, f_name):
        return f_name in self._pack or f_name == self.kf.name
