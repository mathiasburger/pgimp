import os
from tempfile import mktemp

import pytest

from pgimp.GimpScriptRunner import GimpScriptRunner, GimpScriptException, GimpScriptExecutionTimeoutException
from pgimp.util import file

gsr = GimpScriptRunner()


def test_execute_file():
    tmpfile = mktemp()
    file.append(tmpfile, 'print(get_parameter("parameter"))')
    out = gsr.execute_file(tmpfile, parameters={'parameter': 'value'}, timeout_in_seconds=1)

    assert 'value\n' == out

    os.remove(tmpfile)


def test_execute_string():
    out = gsr.execute('print("hello")', timeout_in_seconds=1)

    assert "hello\n" == out


def test_runtime_exception():
    with pytest.raises(GimpScriptException):
        gsr.execute('1/0', timeout_in_seconds=1)


def test_pass_parameter():
    result = gsr.execute('print(get_parameter("parameter"))',
                         parameters={'parameter': 'value'}, timeout_in_seconds=1)

    assert 'value\n' == result


def test_timeout():
    with pytest.raises(GimpScriptExecutionTimeoutException):
        gsr.execute('print(', timeout_in_seconds=1)


def test_execute_and_parse_json():
    result = gsr.execute_and_parse_json('return_json(["a", "b", "c"])', timeout_in_seconds=1)

    assert ["a", "b", "c"] == result
