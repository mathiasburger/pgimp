import json
import os
import shutil
import subprocess
import sys
from glob import glob
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
    """
    Indicates that gimp needs to be installed on the system in order for the software to work.
    """
    pass


class GimpScriptException(GimpException):
    """
    Indicates a general error that occurred while trying to execute the script.
    """
    pass


class GimpScriptExecutionTimeoutException(GimpException):
    """
    Thrown when the script execution time exceeds the specified timeout.
    """
    pass


class GimpUnsupportedOSException(GimpException):
    """
    Indicates that your operating system is not supported.
    """
    pass


_path_to_gimp_executable = None


def path_to_gimp_executable():
    global _path_to_gimp_executable

    if _path_to_gimp_executable is not None:
        return _path_to_gimp_executable

    if sys.platform == 'darwin':
        locations = [
            '/Applications/GIMP*.app/Contents/MacOS/gimp',
            '~/Applications/GIMP*.app/Contents/MacOS/gimp',
        ]
        for location in locations:
            location = glob(location)
            if len(location) > 0:
                _path_to_gimp_executable = location[0]
    elif sys.platform == 'linux' or sys.platform == 'linux2':
        _path_to_gimp_executable = shutil.which(EXECUTABLE_GIMP)
    else:
        raise GimpUnsupportedOSException('Your operating system "{:s}" is not supported.'.format(sys.platform))

    return _path_to_gimp_executable


def is_gimp_present():
    return path_to_gimp_executable() is not None


def is_xvfb_present():
    return shutil.which(EXECUTABLE_XVFB) is not None


def strip_gimp_warnings(input):
    # workaround for gimp <2.8.22 that writes warnings to stdout instead of stderr
    if input.startswith('\n(gimp:'):
        to_find = '\n\n(gimp:'
        pos = 0
        while True:
            last_pos = pos
            pos = input.find(to_find, pos + len(to_find))
            if pos == -1:
                output_start = input.find('\n', last_pos + len(to_find))
                if output_start == -1:
                    raise GimpException('Could not find start of output after gimp warnings.')
                output_start += 1
                break
        input = input[output_start:]
    return input


class GimpScriptRunner:
    """
    Executes python2 scripts within gimp's python interpreter and is used to create
    higher-level functionality and abstractions that can be used in python3.

    When the virtual framebuffer xvfb is installed, it will be automatically used
    and no other windowing system is required. This is important for batch jobs on
    machines that do not provide a graphical user interface.

    Example:

    >>> from pgimp.GimpScriptRunner import GimpScriptRunner
    >>> GimpScriptRunner().execute('print("Hello from within gimp")')
    'Hello from within gimp\\n'
    """
    def __init__(self, environment: Dict[str, str]=None, working_directory=os.getcwd()) -> None:
        super().__init__()
        self._gimp_process = None
        self._environment = environment or {}
        self._working_directory = working_directory
        self._file_to_execute = None

    def execute_file(self, file: str, *, parameters: dict=None, timeout_in_seconds: float=None, output_stream: FileIO = None, error_stream: FileIO = None) -> Union[str, None]:
        """
        Execute a script from a file within gimp's python interpreter.

        Example:

        >>> from pgimp.GimpScriptRunner import GimpScriptRunner
        >>> from pgimp.util.file import relative_to
        >>> GimpScriptRunner().execute_file(relative_to(__file__, 'test-resources/hello.py'))
        'Hello from within gimp\\n'

        See also :py:meth:`~pgimp.GimpScriptRunner.GimpScriptRunner.execute`.
        """
        self._file_to_execute = file
        parameters = parameters or {}
        try:
            result = self.execute(
                'from pgimp.gimp.parameter import get_parameter; exec(open(get_parameter("__script_file__")).read(), globals())',
                {**parameters, '__script_file__': file},
                timeout_in_seconds,
                output_stream=output_stream,
                error_stream=error_stream
            )
            return result
        finally:
            self._file_to_execute = None

    def execute_and_parse_json(self, string: str, parameters: dict=None, timeout_in_seconds: float=None, error_stream: FileIO = None) -> JsonType:
        """
        Execute a given piece of code within gimp's python interpreter and decode the result to json.

        Example:

        >>> from pgimp.GimpScriptRunner import GimpScriptRunner
        >>> GimpScriptRunner().execute_and_parse_json(
        ...     'from pgimp.gimp.parameter import return_json; return_json({"a": "b", "c": [1, 2]})'
        ... )['c']
        [1, 2]

        See also :py:meth:`~pgimp.GimpScriptRunner.GimpScriptRunner.execute`.
        """
        result = self.execute(
            string,
            parameters=parameters,
            timeout_in_seconds=timeout_in_seconds,
            error_stream=error_stream
        )
        return self._parse(result)

    def execute_and_parse_bool(self, string: str, parameters: dict=None, timeout_in_seconds: float=None, error_stream: FileIO = None) -> bool:
        """
        Execute a given piece of code within gimp's python interpreter and decode the result to bool.

        Example:

        >>> from pgimp.GimpScriptRunner import GimpScriptRunner
        >>> GimpScriptRunner().execute_and_parse_bool(
        ...     'from pgimp.gimp.parameter import return_bool; return_bool("truthy")'
        ... )
        True

        See also :py:meth:`~pgimp.GimpScriptRunner.GimpScriptRunner.execute`.
        """
        result = self.execute(
            string,
            parameters=parameters,
            timeout_in_seconds=timeout_in_seconds,
            error_stream=error_stream
        )
        return self._parse(result)

    def execute_binary(self, string: str, parameters: dict=None, timeout_in_seconds: float=None, error_stream: FileIO = None) -> bytes:
        """
        Execute a given piece of code within gimp's python interpreter and decode the result to bytes.

        Example:

        >>> import numpy as np
        >>> from pgimp.GimpScriptRunner import GimpScriptRunner
        >>> print(
        ...     np.frombuffer(
        ...         GimpScriptRunner().execute_binary(
        ...             "from pgimp.gimp.parameter import *; import sys; sys.stdout.write(get_bytes('arr'))",
        ...             parameters={"arr": np.array([i for i in range(0, 3)], dtype=np.uint8).tobytes()}),
        ...             dtype=np.uint8
        ...     )
        ... )
        [0 1 2]

        See also :py:meth:`~pgimp.GimpScriptRunner.GimpScriptRunner.execute`.

        :return: Raw bytes to be decoded to your target type.
        """
        return self._send_to_gimp(
            string,
            timeout_in_seconds,
            binary=True,
            parameters=parameters,
            error_stream=error_stream
        )

    def execute(
        self,
        string: str,
        parameters: Dict[str, Union[bool, int, float, str, bytes, list, tuple, dict]]=None,
        timeout_in_seconds: float=None,
        output_stream: FileIO = None,
        error_stream: FileIO = None
    ) -> Union[str, None]:
        """
        Execute a given piece of code within gimp's python interpreter.

        Example:

        >>> from pgimp.GimpScriptRunner import GimpScriptRunner
        >>> GimpScriptRunner().execute('print("Hello from within gimp")')
        'Hello from within gimp\\n'

        :param string: The code to be executed as string.
        :param parameters: Parameter names and values. Supported types will be encoded as string, be passed to the script and be decoded there.
        :param timeout_in_seconds: How long to wait for completion in seconds until a :py:class:`~pgimp.GimpScriptRunner.GimpScriptExecutionTimeoutException` is thrown.
        :param output_stream: If absent, the method will return the output, otherwise it will be written diretcly to the stream.
        :param error_stream: If absent, an exception will be thrown if errors occur. Otherwise errors will be written directly to the stream.
        :return: The output produced by the script if no output stream is defined.
        """
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
        command.append(path_to_gimp_executable())
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
        parameters_parsed = {}
        for parameter, value in parameters.items():
            if isinstance(value, str):
                parameters_parsed[parameter] = value
            elif isinstance(value, bool) or isinstance(value, int) or isinstance(value, float) or isinstance(value, bytes):
                parameters_parsed[parameter] = repr(value)
            elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, dict):
                parameters_parsed[parameter] = json.dumps(value)
            else:
                raise GimpScriptException('Cannot interpret parameter type {:s}'.format(type(value).__name__))

        gimp_environment.update({k: v for k, v in parameters_parsed.items() if parameters_parsed[k] is not None})

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
                error_string = stderr_content.rsplit('\n', 1)[0] + '\n'
                if self._file_to_execute:
                    error_string = error_string.replace('File "<string>"', 'File "{:s}"'.format(self._file_to_execute), 1)
                raise GimpScriptException(error_string)

        return strip_gimp_warnings(stdout_content)

    def _parse(self, input: str) -> JsonType:
        return json.loads(input)
