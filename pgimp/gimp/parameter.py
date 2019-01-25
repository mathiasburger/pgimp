# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import json
import os
import sys

import gimp


def get_parameter(name, default=None):
    """
    :type name: str
    """
    if default is not None and name not in os.environ:
        return default
    return os.environ[name]


def get_bool(name, default=None):
    """
    :type name: str
    :type default: bool
    :rtype: bool
    """
    value = get_parameter(name, default)
    if isinstance(value, bool):
        return value
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError("Could not decode '" + str(value) + "' to boolean")


def get_int(name, default=None):
    """
    :type name: str
    :type default: int
    :rtype: int
    """
    return int(get_parameter(name, default))


def get_float(name, default=None):
    """
    :type name: str
    :type default: float
    :rtype: float
    """
    return float(get_parameter(name, default))


def get_string(name, default=None):
    """
    :type name: str
    :type default: str
    :rtype: str
    """
    return get_parameter(name, default)


def get_bytes(name, default=None):
    """
    :type name: str
    :type default: bytes
    :rtype: bytes
    """
    return eval(get_parameter(name, default))


def get_json(name, default=None):
    """
    :type name: str
    :type default: str
    :rtype: None or bool or int or float or str or list or dict
    """
    return json.loads(get_parameter(name, default))


def return_json(obj):
    """
    :type obj: None or bool or int or float or str or list or dict
    """
    json.dump(obj, sys.stdout)
    gimp.pdb.gimp_quit(0)


def return_bool(bool):
    """
    :param bool: bool
    """
    print('true' if bool else 'false')
    gimp.pdb.gimp_quit(0)
