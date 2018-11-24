# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import numpy as np
import pytest

from pgimp.GimpScriptRunner import GimpScriptRunner, GimpScriptException

gsr = GimpScriptRunner()


@pytest.mark.parametrize("test_input,expected", [
    (True, "True"),
    (False, "False"),
])
def test_get_bool(test_input, expected):
    out = gsr.execute(
        "from pgimp.gimp.parameter import *; import sys; print(get_bool('param'))",
        parameters={'param': test_input},
        timeout_in_seconds=1
    )

    assert "{:s}\n".format(expected) == out


def test_get_int():
    out = gsr.execute(
        "from pgimp.gimp.parameter import *; import sys; print(get_int('param'))",
        parameters={'param': 21},
        timeout_in_seconds=1
    )

    assert "21\n" == out


def test_get_float():
    out = gsr.execute(
        "from pgimp.gimp.parameter import *; import sys; print(get_float('param'))",
        parameters={'param': 21.123},
        timeout_in_seconds=1
    )

    assert "21.123\n" == out


def test_get_string():
    out = gsr.execute(
        "from pgimp.gimp.parameter import *; import sys; print(get_string('param'))",
        parameters={'param': 'abc'},
        timeout_in_seconds=1
    )

    assert "abc\n" == out


def test_get_bytes():
    arr = np.array([i for i in range(0, 255)], dtype=np.uint8)

    out = gsr.execute_binary(
        "from pgimp.gimp.parameter import *; import sys; sys.stdout.write(get_bytes('param'))",
        parameters={'param': arr.tobytes()},
        timeout_in_seconds=1
    )

    assert np.all(arr == np.frombuffer(out, dtype=np.uint8))


def test_get_json():
    json = {'a': 1, 'b': 1.1, 'c': [1, 2, 3], 'd': {'e': 'val'}}
    out = gsr.execute_and_parse_json(
        "from pgimp.gimp.parameter import *; return_json(get_json('param'))",
        parameters={'param': json},
        timeout_in_seconds=1
    )

    assert json == out


def test_get_unknown_type():
    with pytest.raises(GimpScriptException) as e:
        gsr.execute(
            "from pgimp.gimp.parameter import *; import sys; sys.stdout.write(get_json('param'))",
            parameters={'param': object()},
            timeout_in_seconds=1
        )

    assert 'Cannot interpret parameter type object' == str(e.value)
