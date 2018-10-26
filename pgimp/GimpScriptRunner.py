import os
import shutil
import subprocess
from typing import Dict, Tuple

from pgimp.GimpException import GimpException
from pgimp.util import file

EXECUTABLE_GIMP = 'gimp'
EXECUTABLE_XVFB = 'xvfb-run'

FLAG_NO_INTERFACE = '-i'
FLAG_PYTHON_INTERPRETER = '--batch-interpreter=python-fu-eval'
FLAG_NO_DATA = '-d'
FLAG_NO_FONTS = '-f'
FLAG_NON_INTERACTIVE = '-b'
FLAG_FROM_STDIN = '-'


class GimpNotInstalledException(GimpException):
    pass


class GimpNotRunningException(GimpException):
    pass


class GimpScriptException(GimpException):
    pass


def is_gimp_present():
    return shutil.which(EXECUTABLE_GIMP) is not None


def is_xvfb_present():
    return shutil.which(EXECUTABLE_XVFB) is not None


class GimpScriptRunner:
    def __init__(self, environment: Dict[str, str]=None, working_directory=os.getcwd()) -> None:
        super().__init__()
        self._gimp_process: subprocess.Popen = None
        self._environment = environment or {}
        self._working_directory = working_directory

    def execute_file(self, file: str, timeout_in_seconds: float=None) -> Tuple[str, str]:
        with open(file, 'r') as file_handle:
            content = file_handle.read()
        return self.execute_string(content, timeout_in_seconds)

    def execute_string(self, string: str, timeout_in_seconds: float=None) -> Tuple[str, str]:
        self._open_gimp()
        return self._send_to_gimp(string, timeout_in_seconds)

    def _open_gimp(self):
        if not is_gimp_present():
            raise GimpNotInstalledException('A working gimp installation with gimp on the PATH is necessary.')
        command = []
        if is_xvfb_present():
            command.append(shutil.which('xvfb-run'))
        command.append(shutil.which('gimp'))
        command.extend([
            FLAG_NO_INTERFACE,
            FLAG_NO_DATA,
            FLAG_NO_FONTS,
            FLAG_PYTHON_INTERPRETER,
            FLAG_NON_INTERACTIVE,
            FLAG_FROM_STDIN
        ])

        gimp_environment = {'__working_directory__': self._working_directory}
        gimp_environment.update(os.environ.copy())
        gimp_environment.update({k: v for k, v in self._environment.items() if self._environment[k] is not None})

        self._gimp_process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=gimp_environment,
        )

    def _send_to_gimp(self, code: str, timeout_in_seconds: float=None) -> Tuple[str, str]:
        error_handler = file.get_content(file.relative_to(__file__, 'gimp/error_handler.py')) + "\n"
        quit_gimp = "\npdb.gimp_quit(0)"

        code = error_handler + code + quit_gimp

        stdout, stderr = self._gimp_process.communicate(code.encode(), timeout=timeout_in_seconds)
        stdout_content = stdout.decode()
        stderr_content = stderr.decode()

        error_lines = stderr_content.strip().split('\n')
        if error_lines[-1].startswith('__GIMP_SCRIPT_ERROR__'):
            error_string = stderr_content.rsplit('\n', 1)[0] + '\n'
            raise GimpScriptException(error_string)

        return stdout_content
