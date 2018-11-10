import json
import os
import sys


def get_parameter(name, default=None):
    if default is not None and name not in os.environ:
        return default
    return os.environ[name]


def get_bool(name, default=None):
    value = get_parameter(name, default)
    if isinstance(value, bool):
        return value
    if value == "True":
        return True
    elif value == "False":
        return False
    raise ValueError("Could not decode '" + str(value) + "' to boolean")


def get_int(name, default=None):
    return int(get_parameter(name, default))


def get_float(name, default=None):
    return float(get_parameter(name, default))


def get_string(name, default=None):
    return get_parameter(name, default)


def get_bytes(name, default=None):
    return eval(get_parameter(name, default))


def get_json(name, default=None):
    return json.loads(get_parameter(name, default))


def return_json(obj):
    json.dump(obj, sys.stdout)
