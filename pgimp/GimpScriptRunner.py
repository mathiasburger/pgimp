import json
import os
import shutil
import subprocess
from io import FileIO
from typing import Dict, Union

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

JsonType = Union[None, bool, int, float, str, list, dict]


class GimpNotInstalledException(GimpException):
    pass


class GimpNotRunningException(GimpException):
    pass


class GimpScriptException(GimpException):
    pass


class GimpScriptExecutionTimeoutException(GimpException):
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
        self._file_to_execute = None

    def execute_file(self, file: str, *, parameters: dict=None, timeout_in_seconds: float=None, output_stream: FileIO = None, error_stream: FileIO = None) -> Union[str, None]:
        self._file_to_execute = file
        try:
            result = self.execute(
                'exec(open(get_parameter("__script_file__")).read(), globals())',
                {**parameters, '__script_file__': file},
                timeout_in_seconds,
                output_stream=output_stream,
                error_stream=error_stream
            )
            return result
        finally:
            self._file_to_execute = None

    def execute_and_parse_json(self, string: str, timeout_in_seconds: float=None, error_stream: FileIO = None) -> JsonType:
        result = self.execute(
            string,
            timeout_in_seconds=timeout_in_seconds,
            error_stream=error_stream
        )
        return self._parse(result)

    def execute_binary(self, string: str, parameters: dict=None, timeout_in_seconds: float=None, error_stream: FileIO = None) -> bytes:
        return self._send_to_gimp(
            string,
            timeout_in_seconds,
            binary=True,
            parameters=parameters,
            error_stream=error_stream
        )

    def execute(self, string: str, parameters: dict=None, timeout_in_seconds: float=None, output_stream: FileIO = None, error_stream: FileIO = None) -> Union[str, None]:
        return self._send_to_gimp(
            string,
            timeout_in_seconds,
            parameters=parameters,
            output_stream=output_stream,
            error_stream=error_stream
        )

    def _send_to_gimp(
        self,
        code: str,
        timeout_in_seconds: float=None,
        binary=False,
        parameters: dict=None,
        output_stream: FileIO = None,
        error_stream: FileIO = None
    ) -> Union[str, bytes, None]:

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

        parameters = parameters or {}
        gimp_environment.update({k: v for k, v in parameters.items() if parameters[k] is not None})

        self._gimp_process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=output_stream if output_stream else subprocess.PIPE,
            stderr=error_stream if error_stream else subprocess.PIPE,
            env=gimp_environment,
        )

        initializer = file.get_content(file.relative_to(__file__, 'gimp/initializer.py')) + '\n'
        extend_path = "sys.path.append('{:s}')\n".format(os.path.dirname(os.path.dirname(__file__)))
        quit_gimp = '\npdb.gimp_quit(0)'

        code = initializer + extend_path + code + quit_gimp

        try:
            stdout, stderr = self._gimp_process.communicate(code.encode(), timeout=timeout_in_seconds)
        except subprocess.TimeoutExpired as exception:
            raise GimpScriptExecutionTimeoutException(str(exception) + '\nCode that was executed:\n' + code)

        if binary:
            stdout_content = stdout
        elif output_stream:
            stdout_content = None
            output_stream.close()
        else:
            stdout_content = stdout.decode()

        if error_stream:
            stderr_content = None
            error_stream.close()
        else:
            stderr_content = stderr.decode()

        if stderr_content:
            error_lines = stderr_content.strip().split('\n')
            if error_lines[-1].startswith('__GIMP_SCRIPT_ERROR__'):
                error_string: str = stderr_content.rsplit('\n', 1)[0] + '\n'
                if self._file_to_execute:
                    error_string = error_string.replace('File "<string>"', 'File "{:s}"'.format(self._file_to_execute), 1)
                raise GimpScriptException(error_string)

        return stdout_content

    def _parse(self, input: str) -> JsonType:
       return json.loads(input)
