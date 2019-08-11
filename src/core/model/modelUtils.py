# -*- coding:utf-8 -*-

from src.core.model.modelTypeBase import ModelTypeBase
from src.core.model.modelCounter import ModelCounter
from src.core.model.modelPb import ModelPb, ModelPbHash
from src.core.model.modelSimple import ModelSimple


def get_models_list():
    ret = {}
    for k, v in ModelTypeBase.models.iteritems():
        ret[k] = "{} Base:{}".format(str(v.key_field) if hasattr(v, 'key_field') else str(None),
                                     ",".join(map(lambda x: x.__name__, v.__bases__)))
    return ret


def get_model_pb(name, key):
    models = ModelTypeBase.models
    if name not in models:
        return "{} is not model type".format(name), None

    model_cls = models[name]
    if not issubclass(model_cls, ModelPb) and not issubclass(model_cls, ModelPbHash):
        return "{} is not model pb or pbhash".format(name), None

    obj = model_cls.get(key)
    if obj is None:
        return "{} key:{} not exist".format(model_cls, key), None

    return None, obj.pbobj


def get_model_detail(name, key):
    models = ModelTypeBase.models
    if name not in models:
        return -2, None

    model_cls = models[name]
    if issubclass(model_cls, ModelCounter):
        if hasattr(model_cls, 'counter_field'):
            return 0, model_cls.current
        else:
            return -3, None

    obj = model_cls.get(key)
    if obj is None:
        return -1, None

    if issubclass(model_cls, ModelPb) or issubclass(model_cls, ModelPbHash):
        return 0, obj.pbobj

    if issubclass(model_cls, ModelSimple):
        return 0, obj.data

    return 0, obj.get_all()


def lock(*keys):
    return ModelTypeBase.locker.dist_lock(*keys)

