import os
import tempfile
from io import FileIO
from tempfile import mktemp

import pytest

from pgimp.GimpScriptRunner import GimpScriptRunner, GimpScriptException, GimpScriptExecutionTimeoutException
from pgimp.util import file

gsr = GimpScriptRunner()


def test_execute_file():
    tmpfile = mktemp()
    file.append(tmpfile, 'print(get_parameter("parameter"))')
    out = gsr.execute_file(tmpfile, parameters={'parameter': 'value'}, timeout_in_seconds=1)

    os.remove(tmpfile)

    assert 'value\n' == out


def test_execute_file_with_runtime_exception():
    tmpfile = mktemp(suffix='.py')
    file.append(tmpfile, 'print(get_parameter("parameter"))\nprint(1/0)')

    with pytest.raises(GimpScriptException) as exception:
        gsr.execute_file(tmpfile, parameters={'parameter': 'value'}, timeout_in_seconds=1)

    original_exception = exception._excinfo[1]
    exception_lines = str(original_exception).split('\n')

    os.remove(tmpfile)

    assert 'File "{:s}", line 2'.format(tmpfile) in exception_lines[-3]


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


def test_import_from_pgimp_library():
    gimp_file = file.relative_to(__file__, 'test-resources/rgb.xcf')
    out = gsr.execute('from pgimp.gimp.file import *\nimage = open_xcf(\'{:s}\')\nprint(image.layers[0].name)'.format(gimp_file), timeout_in_seconds=1)

    assert 'Blue\n' == out


def test_execute_with_output_stream():
    tmpfile = tempfile.mktemp()

    stream = FileIO(tmpfile, 'w')
    out = gsr.execute(
        "import time; time.sleep(1); print('1'); time.sleep(1); print('2'); time.sleep(1); print('3')",
        output_stream=stream
    )

    assert out is None
    assert stream.closed
    with open(tmpfile, 'r') as fh:
        assert '1\n2\n3\n' == fh.read()

    os.remove(tmpfile)


def test_execute_with_error_stream():
    tmpfile = tempfile.mktemp()

    stream = FileIO(tmpfile, 'w')
    out = gsr.execute(
        "print('1'); print('2'); print('3'); 1/0",
        error_stream=stream
    )

    assert '1\n2\n3\n' == out
    assert stream.closed
    with open(tmpfile, 'r') as fh:
        assert fh.read().endswith('__GIMP_SCRIPT_ERROR__ 1')

    os.remove(tmpfile)
