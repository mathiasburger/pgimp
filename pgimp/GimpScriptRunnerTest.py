# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import tempfile
from io import FileIO
from tempfile import mktemp

import numpy as np
import pytest

from pgimp.GimpScriptRunner import GimpScriptRunner, GimpScriptException, GimpScriptExecutionTimeoutException, \
    strip_gimp_warnings, strip_initialization_warnings, python2_pythonpath
from pgimp.util import file
from pgimp.util.TempFile import TempFile

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
        assert '1\n2\n3\n' == strip_gimp_warnings(fh.read())

    os.remove(tmpfile)


def test_execute_with_error_stream():
    with TempFile() as tmpfile:
        stream = FileIO(tmpfile, 'w')

        try:
            out = gsr.execute(
                "print('1'); print('2'); print('3'); 1/0",
                error_stream=stream
            )

            assert '1\n2\n3\n' == out
            assert stream.closed

            with open(tmpfile, 'r') as fh:
                assert fh.read().endswith('__GIMP_SCRIPT_ERROR__ 1')
        except GimpScriptException as e:
            # gimp prior to 2.8.22 writes stderr to stdout and an error in stdout will cause an exception
            # and stderr will be empty

            exception_message = strip_gimp_warnings(str(e))
            assert exception_message.startswith('1\n2\n3\nTraceback')
            assert exception_message.endswith('ZeroDivisionError: integer division or modulo by zero\n')

            with open(tmpfile, 'r') as fh:
                assert fh.read().endswith('')


def test_execute_binary():
    arr = np.frombuffer(GimpScriptRunner().execute_binary(
        "from pgimp.gimp.parameter import *; import sys; sys.stdout.write(get_bytes('arr'))",
        parameters = {"arr": np.array([i for i in range(0, 3)], dtype=np.uint8).tobytes()}),
        dtype=np.uint8
    )
    assert np.all([0, 1, 2] == arr)


def test_strip_gimp_warnings():
    warnings = '\n(gimp:5857): GLib-GObject-WARNING **: g_object_set_valist: object class \'GeglConfig\' has no ' \
               'property named \'cache-size\'\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING **: Cannot change name ' \
               'of operation class 0x28E1A00 from "gimp:point-layer-mode" to "gimp:dissolve-mode"\n\n(gimp:5857): ' \
               'GEGL-gegl-operation.c-WARNING **: Cannot change name of operation class 0x28E1E10 from ' \
               '"gimp:point-layer-mode" to "gimp:behind-mode"\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING **: ' \
               'Cannot change name of operation class 0x28E2200 from "gimp:point-layer-mode" to "gimp:multiply-mode"' \
               '\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING **: Cannot change name of operation class 0x28E3250 ' \
               'from "gimp:point-layer-mode" to "gimp:screen-mode"\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING **:' \
               ' Cannot change name of operation class 0x28E3620 from "gimp:point-layer-mode" to "gimp:overlay-mode"' \
               '\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING **: Cannot change name of operation class 0x28E3A50 ' \
               'from "gimp:point-layer-mode" to "gimp:difference-mode"\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING' \
               ' **: Cannot change name of operation class 0x28E3E10 from "gimp:point-layer-mode" to '\
               '"gimp:addition-mode"\n\n(gimp:5857): GEGL-gegl-operation.c-WARNING **: Cannot change name of ' \
               'operation class 0x28E4250 from "gimp:point-layer-mode" to "gimp:subtract-mode"\n\n(gimp:5857): ' \
               'GEGL-gegl-operation.c-WARNING **: Cannot change name of operation class 0x28E4640 from ' \
               '"gimp:point-layer-mode" to "gimp:darken-only-mode"\n'

    desired_output = ' my result\n\nblah'

    input = warnings + desired_output
    assert desired_output == strip_gimp_warnings(input)

    desired_output = '(gimp:THIS SHOULD NOT BE EXCLUDED BECAUSE OF ONLY ONE NEWLINE INSTEAD OF TWO\n\nblah'

    input = warnings + desired_output
    assert desired_output == strip_gimp_warnings(input)


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


def test_strip_initialization_warnings():
    error = ('Missing fast-path babl conversion detected, Implementing missing babl fast paths\n'
             'accelerates GEGL, GIMP and other software using babl, warnings are printed on\n'
             'first occurance of formats used where a conversion has to be synthesized\n'
             'programmatically by babl based on format description\n'
             '\n'
             '*WARNING* missing babl fast path(s): "R\'G\'B\' double" to "CIE Lab double"\n')
    error_lines = error.split('\n')
    error_lines = strip_initialization_warnings(error_lines)

    assert not error_lines

    error += 'abc'
    error_lines = error.split('\n')
    error_lines = strip_initialization_warnings(error_lines)

    assert ['abc'] == error_lines


def test_python2_pythonpath():
    assert 'site-packages' in python2_pythonpath() or 'dist-packages' in python2_pythonpath()
