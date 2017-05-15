"""
Application Data

Simple K/V store for application data. 

"""

import copy
from mocha import (db, utils)

def make_key(key):
    return utils.slugify(key)


def get(key, node=None, default=None):
    """
    Retrieve data
    :param key: 
    :param node: the node_key or the dot notation key to retrieve sub data
            get('myapp', 'this.is.a.nested.dict.data')
            get('my_other_data')
    :param default:
    :return: dict_dot dict object
    """
    d = AppData.get_by_key(key)
    if d:
        data = utils.dict_dot(d)
        return data.get(node, default) if node else data
    return {}


def set(key, value={}, reset=False, init=False):
    """
    Set data
    :param key: A unique to set, best to use __name__
    :param value: dict - the value to save
    :param reset: bool - If true, it will reset the value to the current one. 
                 if False, it will just update the stored value with the current
                 one
    :param init: bool - If True, it will create the entry if it doesn't exits
                 next time invoked, it will not save anything
    :return: 
    """
    if not isinstance(value, dict):
        raise ValueError("App Data value must be a dict")

    k = AppData.get_by_key(key, True)
    if not k:
        AppData.create(key=make_key(key), value=value)
    else:
        if init is False:
            if reset is False:
                nv = copy.deepcopy(value)
                value = copy.deepcopy(k.value)
                value.update(nv)
            k.update(value=value)


class AppData(db.Model):
    key = db.Column(db.String(255), index=True, unique=True)
    value = db.Column(db.JSONType)

    @classmethod
    def get_by_key(cls, key, as_object=False):
        key = make_key(key)
        r = cls.query().filter(key == key).first()
        return r.value if r and as_object is False else r

