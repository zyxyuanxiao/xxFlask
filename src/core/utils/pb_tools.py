# -*- coding:utf-8 -*-

import json
import inspect
import struct
import cStringIO
import pbx
import ujson

PB_MODULE_DICT = {}
PB_MODULE_OPTIONS = None
_DecodeVarint32 = pbx.decoder._VarintDecoder((1 << 32) - 1, int)
_DecodeVarint = pbx.decoder._VarintDecoder((1 << 64) - 1, long)


def initialize(pb_module_dict):
    global PB_MODULE_OPTIONS

    PB_MODULE_DICT.update(pb_module_dict)
    PB_MODULE_OPTIONS = PB_MODULE_DICT.get("protocol.options_pb2", None)
    if not PB_MODULE_OPTIONS:
        print "PB_MODULE_OPTIONS not initialize."


def set_pb_by_dic(pb, d):
    for k, v in d.iteritems():
        setattr(pb, k, v)


def clone(pb):
    ret = type(pb)()
    ret.CopyFrom(pb)
    return ret


def pb_to_json(pb):
    return pbx.json_format.MessageToJson(pb, True)


def pb_to_dict(pb):
    if ujson:
        return ujson.loads(pb_to_json(pb))

    return json.loads(pb_to_json(pb))


def json_to_pb(pb, json):
    return pbx.json_format.Parse(json, pb, True)


def dict_to_pb(pb, dic):
    if ujson:
        return json_to_pb(pb, ujson.dumps(dic))

    return json_to_pb(pb, json.dumps(dic))


MIX_PB_TO_DIC_LIST = {
    (pbx.Message, lambda d: pb_to_dict(d)),
    (list, lambda d: [mix_to_dict(obj) for obj in d]),
    (dict, lambda d: {k: mix_to_dict(v) for k, v in d.iteritems()}),
    (pbx.RepeatedCompositeContainer, lambda d: [mix_to_dict(obj) for obj in d]),
    (pbx.RepeatedScalarContainer, lambda d: [obj for obj in d]),
    (pbx.MessageMapContainer, lambda d: {mix_to_dict(k): mix_to_dict(d[k]) for k in d})
}


def mix_to_dict(d):
    return next((f(d) for k, f in MIX_PB_TO_DIC_LIST if isinstance(d, k)), d)


TYPE_DICT = dict()
TYPE_DICT[pbx.FieldDescriptor.TYPE_INT64] = long
TYPE_DICT[pbx.FieldDescriptor.TYPE_UINT64] = long
TYPE_DICT[pbx.FieldDescriptor.TYPE_UINT32] = long
TYPE_DICT[pbx.FieldDescriptor.TYPE_SFIXED64] = long
TYPE_DICT[pbx.FieldDescriptor.TYPE_SINT64] = long
TYPE_DICT[pbx.FieldDescriptor.TYPE_FIXED64] = long
TYPE_DICT[pbx.FieldDescriptor.TYPE_INT32] = int
TYPE_DICT[pbx.FieldDescriptor.TYPE_SINT32] = int
TYPE_DICT[pbx.FieldDescriptor.TYPE_SFIXED32] = int
TYPE_DICT[pbx.FieldDescriptor.TYPE_FIXED32] = int
TYPE_DICT[pbx.FieldDescriptor.TYPE_FLOAT] = float
TYPE_DICT[pbx.FieldDescriptor.TYPE_DOUBLE] = float
TYPE_DICT[pbx.FieldDescriptor.TYPE_BOOL] = bool
TYPE_DICT[pbx.FieldDescriptor.TYPE_STRING] = str
TYPE_DICT[pbx.FieldDescriptor.TYPE_BYTES] = str

TYPE_NAME_DIC = dict()
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_DOUBLE] = 'double'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_FLOAT] = 'float'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_INT64] = 'int64'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_UINT64] = 'uint64'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_INT32] = 'int32'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_FIXED64] = 'fixed64'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_FIXED32] = 'fixed32'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_BOOL] = 'bool'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_STRING] = 'string'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_GROUP] = 'group'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_MESSAGE] = 'message'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_BYTES] = 'bytes'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_UINT32] = 'uint32'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_ENUM] = 'enum'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_SFIXED32] = 'sfixed32'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_SFIXED64] = 'sfixed64'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_SINT32] = 'sint32'
TYPE_NAME_DIC[pbx.FieldDescriptor.TYPE_SINT64] = 'sint64'


def scalar_to_packed(fd, v):
    if fd.type == pbx.FieldDescriptor.TYPE_BOOL:
        return '1' if v else '0'
    return str(v)


def packed_to_scalar(fd, packed):
    if fd.type == pbx.FieldDescriptor.TYPE_BOOL:
        return packed == '1' or packed == 'True'
    return type(fd.default_value)(packed)


def is_scalar(fd):
    return fd.label != pbx.FieldDescriptor.LABEL_REPEATED and fd.type in TYPE_DICT


# param is field_descryptor type ,
# reference in https://developers.google.com/protocol-buffers/docs/reference/python/ field desctyptor
def scalar_type(ft):
    return TYPE_DICT[ft]


# fc is a self-define proto extension
def get_field_comment(f):
    c = next((d for l, d in f.GetOptions().ListFields() if l.name == 'fc'), None)
    if c is None:
        if is_pb_map(f):
            c = 'map'
    return c


#
# hide_desc is a self-define proto extension
#
def is_field_hide(f):
    c = next((d for l, d in f.GetOptions().ListFields() if l.name == 'hide_desc'), None)
    return c is not None


def scalar_type_name(f):
    ft = f.type
    comment = get_field_comment(f)
    if comment:
        return u'{}({})'.format(TYPE_NAME_DIC[ft], comment)
    else:
        return TYPE_NAME_DIC[ft]


def str_under_to_camal_case(input_str):
    if len(input_str) == 0:
        return input_str
    l_list = input_str.split('_')
    ret = l_list[0]
    for i in range(1, len(l_list)):
        ret = ret + (l_list[i].capitalize())
    return ret


def is_pb_map(f):
    return (f.message_type and
            f.message_type.has_options and
            f.message_type.GetOptions().map_entry)


def display_name(f, camel):
    n = f.camelcase_name if camel else f.name
    if f.label == pbx.FieldDescriptor.LABEL_REPEATED or f.type == pbx.FieldDescriptor.TYPE_MESSAGE:
        comment = get_field_comment(f)
        if comment:
            return '{}({})'.format(n, comment)
    return n


def get_oneof_base(f, desc):
    for oneof in desc.oneofs:
        if f in oneof.fields:
            return oneof
    return None


def add_field_to_dic(d, f, camel, message_type, mts):
    fname_display = display_name(f, camel)

    if is_field_hide(f):
        return
    if f.label == pbx.FieldDescriptor.LABEL_REPEATED:
        if f.type == pbx.FieldDescriptor.TYPE_MESSAGE:
            if f.message_type in mts:
                d[fname_display] = ['(recursive {})'.format(mts[f.message_type])]
            else:
                mts[f.message_type] = fname_display
                sub_dic = {}
                if is_pb_map(f):
                    kf = [x for x in f.message_type.fields if x.name == 'key'][0]
                    vf = [x for x in f.message_type.fields if x.name == 'value'][0]
                    dic_map = {}
                    add_field_to_dic(dic_map, vf, camel, f.message_type, mts)
                    sub_dic[scalar_type_name(kf) + '(key of map)'] = dic_map['value']
                    d[fname_display] = sub_dic
                else:
                    for subf in f.message_type.fields:
                        add_field_to_dic(sub_dic, subf, camel, f.message_type, mts)
                    d[fname_display] = [sub_dic]
                del mts[f.message_type]
        else:
            d[fname_display] = [scalar_type_name(f)]
    elif f.type == pbx.FieldDescriptor.TYPE_MESSAGE:
        if f.message_type in mts:
            d[fname_display] = '(recursive {})'.format(mts[f.message_type])
        else:
            mts[f.message_type] = fname_display
            oneof = get_oneof_base(f, message_type)
            if oneof:
                fname_display = '{}(oneof {})'.format(fname_display, oneof.name)
            sub_dic = {}
            for subf in f.message_type.fields:
                add_field_to_dic(sub_dic, subf, camel, f.message_type, mts)
            d[fname_display] = sub_dic
            del mts[f.message_type]
    elif f.type == pbx.FieldDescriptor.TYPE_ENUM:
        d[fname_display] = f.enum_type.name
    else:
        d[fname_display] = scalar_type_name(f)


def add_enum_to_dic(d, v):
    field_name = v.name
    v_comment = ''
    v_value = v.number
    for oK, oV in v.GetOptions().ListFields():
        if oK.name == 'evc':
            v_comment = oV
    d[field_name] = v_value, v_comment


def descriptor_to_dict(desc, camel):
    dic = {}

    if isinstance(desc, pbx.EnumDescriptor):
        for v in desc.values:
            add_enum_to_dic(dic, v)
    else:
        for f in desc.fields:
            add_field_to_dic(dic, f, camel, desc, {})
    return dic


def descriptor_inner_type_to_dict(desc, camel):
    dic = {}
    inner_names = []
    if not isinstance(desc, pbx.EnumDescriptor):
        for inner in desc.nested_types:
            if len(inner.fields) == 1 and inner.fields[0].name == inner.name:
                dic.update(descriptor_to_dict(inner, camel))
                inner_names.append(inner.name)
        for inner in desc.nested_types:
            if inner.name not in inner_names:
                dic[inner.name] = descriptor_to_dict(inner, camel)
    return dic


def msg_types(*pb_modules):
    ret = []
    for pbm in pb_modules:
        for name, type_instance in inspect.getmembers(pbm):
            if inspect.isclass(type_instance) and issubclass(type_instance, pbx.Message):
                ret.append(type_instance)
    return ret


def split_res_bin(file_name):
    with open(file_name, "rb") as FILE:
        s = FILE.read()
        ss = cStringIO.StringIO(s)
        while True:
            length_str = ss.read(4)
            if length_str:
                length = struct.unpack('I', length_str)[0]
                yield ss.read(length)
            else:
                break
        ss.close()


def batch_parse(packed_data_list, pb_type):
    ret = []
    for d in packed_data_list:
        ins = pb_type()
        ins.ParseFromString(d)
        ret.append(ins)
    return ret


def load_res_bin(file_name, pb_type):
    datalist = split_res_bin(file_name)
    return batch_parse(datalist, pb_type)


def message_serialize_dict(pbmsg):
    packed = pbmsg.SerializeToString()
    totallen = len(packed)
    new_pos = 0
    ret_dict = {}
    while new_pos < totallen:
        tag_bytes, next_pos = pbx.decoder.ReadTag(packed, new_pos)
        tag_int, _ = _DecodeVarint32(tag_bytes, 0)
        field_number, wire_type = pbx.wire_format.UnpackTag(tag_int)
        next_pos = pbx.decoder.SkipField(packed, next_pos, totallen, tag_bytes)
        ev = ret_dict.get(field_number)
        if ev:
            ret_dict[field_number] = ev + packed[new_pos:next_pos]
        else:
            ret_dict[field_number] = packed[new_pos:next_pos]
        new_pos = next_pos
        if new_pos < 0:
            raise Exception('pb encode error!{} {}'.format(type(pbmsg), pbmsg))
    assert (new_pos == totallen)
    return ret_dict


# this can only untag message type
def untag_raw_pbdata(data_with_tag):
    if data_with_tag:
        tag_bytes, next_pos = pbx.decoder.ReadTag(data_with_tag, 0)
        size, next_pos = _DecodeVarint(data_with_tag, next_pos)
        return data_with_tag[next_pos:]
    else:
        return ''


# options_pb2 about......
def res_keys(desc, camel):
    keys = []
    for f in desc.fields:
        if f.GetOptions().Extensions[PB_MODULE_OPTIONS.pk]:
            keys.append(f.camelcase_name if camel else f.name)
    return keys


key_getter_dict = {}


def res_key_getter(pbtype):
    func = key_getter_dict.get(pbtype)
    if not func:
        keynames = [fd.name for fd in pbtype.DESCRIPTOR.fields if fd.GetOptions().Extensions[PB_MODULE_OPTIONS.pk]]
        if len(keynames) == 0:
            def getter(pbobj):
                return None
        elif len(keynames) == 1:
            def getter(pbobj):
                return getattr(pbobj, keynames[0])
        else:
            def getter(pbobj):
                return tuple(getattr(pbobj, name) for name in keynames)
        func = getter
        key_getter_dict[pbtype] = getter
    return func
