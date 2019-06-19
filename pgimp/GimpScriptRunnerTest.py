# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
from tempfile import mktemp

import numpy as np
import pytest

from pgimp.GimpScriptRunner import GimpScriptRunner, GimpScriptException, GimpScriptExecutionTimeoutException, \
    python2_pythonpath
from pgimp.util import file

gsr = GimpScriptRunner()


def test_execute_file():
    tmpfile = mktemp()
    file.append(tmpfile, 'from pgimp.gimp.parameter import get_parameter; print(get_parameter("parameter"))')
    out = gsr.execute_file(tmpfile, parameters={'parameter': 'value'}, timeout_in_seconds=3)

    os.remove(tmpfile)

    assert 'value\n' == out


def test_execute_file_with_runtime_exception():
    tmpfile = mktemp(suffix='.py')
    file.append(
        tmpfile,
        'from pgimp.gimp.parameter import get_parameter; print(get_parameter("parameter"))\nprint(1/0)'
    )

    with pytest.raises(GimpScriptException) as exception:
        gsr.execute_file(tmpfile, parameters={'parameter': 'value'}, timeout_in_seconds=3)

    original_exception = exception._excinfo[1]
    exception_lines = str(original_exception).split('\n')

    os.remove(tmpfile)

    assert 'File "{:s}", line 2'.format(tmpfile) in exception_lines[-3]


def test_execute_string():
    out = gsr.execute('print("hello")', timeout_in_seconds=3)

    assert "hello\n" == out


def test_runtime_exception():
    with pytest.raises(GimpScriptException):
        gsr.execute('1/0', timeout_in_seconds=1)


def test_pass_parameter():
    result = gsr.execute('from pgimp.gimp.parameter import get_parameter; print(get_parameter("parameter"))',
                         parameters={'parameter': 'value'}, timeout_in_seconds=3)

    assert 'value\n' == result


def test_timeout():
    with pytest.raises(GimpScriptExecutionTimeoutException):
        gsr.execute('print(', timeout_in_seconds=3)


def test_execute_and_parse_json():
    result = gsr.execute_and_parse_json(
        'from pgimp.gimp.parameter import return_json; return_json(["a", "b", "c"])',
        timeout_in_seconds=3
    )

    assert ["a", "b", "c"] == result


def test_execute_and_parse_bool():
    result = gsr.execute_and_parse_json(
        'from pgimp.gimp.parameter import return_bool; return_bool("truthy")',
        timeout_in_seconds=3
    )
    assert result is True

    result = gsr.execute_and_parse_json(
        'from pgimp.gimp.parameter import return_bool; return_bool("")',
        timeout_in_seconds=3
    )
    assert result is False


def test_import_from_pgimp_library():
    gimp_file = file.relative_to(__file__, 'test-resources/rgb.xcf')
    out = gsr.execute(
        'from pgimp.gimp.file import *\nimage = open_xcf(\'{:s}\')\nprint(image.layers[0].name)'.format(gimp_file),
        timeout_in_seconds=3
    )

    assert 'Blue\n' == out


def test_execute_binary():
    arr = np.frombuffer(GimpScriptRunner().execute_binary(
        "from pgimp.gimp.parameter import *; import sys; sys.stdout.write(get_bytes('arr'))",
        parameters = {"arr": np.array([i for i in range(0, 3)], dtype=np.uint8).tobytes()}),
        dtype=np.uint8
    )
    assert np.all([0, 1, 2] == arr)


def test_no_dangling_processes():
    gsr.execute('print()')
    gsr.execute('print()')

    with pytest.raises(GimpScriptExecutionTimeoutException):
        gsr.execute('print(', timeout_in_seconds=3)

    open_processes = os.popen('ps -A | grep -i -e xvfb -e gimp').read().rstrip('\n').split('\n')
    hanging_processes = filter(None, open_processes)
    hanging_processes = filter(lambda x: '<defunct>' not in x, hanging_processes)  # defunct is ok in docker containers
    hanging_processes = list(hanging_processes)

    print('\n'.join(hanging_processes))
    assert len(hanging_processes) == 0


def test_python2_pythonpath():
    assert 'site-packages' in python2_pythonpath() or 'dist-packages' in python2_pythonpath()
