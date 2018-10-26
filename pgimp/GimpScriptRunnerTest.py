import pytest

from pgimp.GimpScriptRunner import GimpScriptRunner, GimpScriptException


def test_execute_string():
    gsr = GimpScriptRunner()
    out = gsr.execute_string('print("hello")', 1)

    assert "hello\n" == out


def test_runtime_exception():
    gsr = GimpScriptRunner()
    with pytest.raises(GimpScriptException):
        gsr.execute_string('1/0', 1)
