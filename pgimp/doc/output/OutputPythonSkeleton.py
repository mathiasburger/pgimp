# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import textwrap
from collections import OrderedDict
from typing import Tuple, MutableMapping, Union, List, Any

from pgimp.doc.GimpDocumentationGenerator import GIMP_TYPE_MAPPING, KNOWN_GIMP_CLASSES, UNKNOWN_GIMP_CLASSES
from pgimp.doc.output.Output import Output
from pgimp.util import file


def pythonify_id(identifier: str):
    return identifier.replace('-', '_')


class OutputPythonSkeleton(Output):
    def __init__(self, output_dir: str) -> None:
        super().__init__()
        self._output_dir = output_dir
        self._current_file = None

    def start_module(self, name: str):
        self._add_file(name)
        self._append('from typing import List, Tuple\n')
        self._append('from gimp import ' + ', '.join(
            [GIMP_TYPE_MAPPING[i] for i in KNOWN_GIMP_CLASSES + UNKNOWN_GIMP_CLASSES]
        ) + '\n')

    def method(
            self,
            method: str,
            description: str,
            parameters: Union[MutableMapping[str, Tuple[str, str]], OrderedDict],
            return_values: Union[MutableMapping[str, Tuple[str, str]], OrderedDict],
    ):
        signature = pythonify_id(method)
        signature += '('
        if parameters:
            last_parameter = next(reversed(parameters))
            for parameter in parameters:
                signature += pythonify_id(parameter)
                signature += ': ' + parameters[parameter][0]
                if parameter != last_parameter:
                    signature += ', '
        signature += ')'
        if return_values:
            signature += ' -> '
            last_return_value = next(reversed(return_values))
            if len(return_values) == 1:
                signature += return_values[last_return_value][0]
            else:
                signature += 'Tuple['
                for return_value in return_values:
                    signature += return_values[return_value][0]
                    if return_value != last_return_value:
                        signature += ', '
                signature += ']'

        documentation = '"""\n'
        if description:
            documentation += description + '\n'
        if description and parameters:
            documentation += '\n'
        if parameters:
            for parameter in parameters:
                documentation += ':param ' + pythonify_id(parameter) + ': ' + parameters[parameter][1] + '\n'
        if return_values:
            documentation += ':return: ' + ', '.join(list(map(pythonify_id, return_values.keys()))) + '\n'
        documentation += '"""'

        result = '\n\ndef ' + signature + ':' + '\n' + textwrap.indent(documentation, '    ') + '\n' + \
                 textwrap.indent('raise NotImplementedError()', '    ') + '\n'

        self._append(result)

    def start_classes(self):
        output_dir_bak = self._output_dir
        self._output_dir = os.path.join(os.path.dirname(self._output_dir), 'gimp')
        self._add_file('__init__')
        self._output_dir = output_dir_bak

        self._append("__all__ = ['pdb']\n")

    def start_class(self, name: str, baseclasses: List[str]):
        self._append('\n\nclass {:s}({:s}):'.format(name, ', '.join(baseclasses)))

    def class_properties(self, properties: List[str]):
        for property in properties:
            self._append(textwrap.indent('\n{:s} = None'.format(property), '    '))

    def class_methods(self, methods: List[str]):
        for method in methods:
            self._append(textwrap.indent(
                '\n\ndef {:s}(self, *args, **kwargs):\n    raise NotImplementedError()'.format(method),
                '    ')
            )
        self._append('\n')

    def start_unknown_class(self, name: str):
        self._append('\n\nclass {:s}:\n    pass\n'.format(name))

    def gimpenums(self, constants: Tuple[str, Any]):
        output_dir_bak = self._output_dir
        self._output_dir = os.path.join(os.path.dirname(self._output_dir), 'gimpenums')
        self._add_file('__init__')
        self._output_dir = output_dir_bak

        output = ''
        for constant_name, constant_value in constants:
            output += '{:s} = {:s}\n'.format(constant_name, repr(constant_value))

        self._append(output)

    def gimpfu_constants(self, constants: Tuple[str, Any]):
        output_dir_bak = self._output_dir
        self._output_dir = os.path.join(os.path.dirname(self._output_dir), 'gimpfu')
        self._add_file('__init__')
        self._output_dir = output_dir_bak

        output = ''
        for constant_name, constant_value in constants:
            output += '{:s} = {:s}\n'.format(constant_name, repr(constant_value))

        self._append(output)

    def _add_file(self, name: str):
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)
        skeleton_file = os.path.join(self._output_dir, '{:s}.py'.format(name))
        if os.path.exists(skeleton_file):
            os.remove(skeleton_file)
        file.touch(skeleton_file)

        self._current_file = skeleton_file

    def _append(self, string: str):
        file.append(self._current_file, string)
