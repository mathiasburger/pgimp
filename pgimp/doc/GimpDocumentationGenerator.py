# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import textwrap
from collections import OrderedDict

from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.doc.output.Output import Output

GIMP_TYPE_MAPPING = {
    0: 'int',  # PDB-INT32 (0)
    1: 'int',  # PDB-INT16 (1)
    2: 'int',  # PDB-INT8 (2)
    3: 'float',  # PDB-FLOAT (3)
    4: 'str',  # PDB-STRING (4)
    5: 'List[int]',  # PDB-INT32ARRAY (5)
    6: 'List[int]',  # PDB-INT16ARRAY (6)
    7: 'List[int]',  # PDB-INT8ARRAY (7)
    8: 'List[float]',  # PDB-FLOATARRAY (8)
    9: 'List[str]',  # PDB-STRINGARRAY (9)
    10: 'Color',  # PDB-COLOR (10)
    11: 'Item',  # PDB-ITEM (11)
    12: 'Display',  # PDB-DISPLAY (12)
    13: 'Image',  # PDB-IMAGE (13)
    14: 'Layer',  # PDB-LAYER (14)
    15: 'Channel',  # PDB-CHANNEL (15)
    16: 'Drawable',  # PDB-DRAWABLE (16)
    17: 'Selection',  # PDB-SELECTION (17)
    18: 'ColorArray',  # PDB-COLORARRAY (18)
    19: 'Vectors',  # PDB-VECTORS (19)
    20: 'Parasite',  # PDB-PARASITE (20)
    21: 'Status',  # PDB-STATUS (21
}
"""
See also gimp-procedural-db-proc-arg doc.
"""

STANDARD_TYPES = list(range(0, 9+1))
UNKNOWN_GIMP_CLASSES = [10, 17, 18, 21]
KNOWN_GIMP_CLASSES = [i for i in GIMP_TYPE_MAPPING if i not in UNKNOWN_GIMP_CLASSES and i not in STANDARD_TYPES]


class GimpDocumentationGenerator:
    def __init__(self, output: Output) -> None:
        super().__init__()
        self._output = output
        self._gsr = GimpScriptRunner()
        self._ordered_gimp_classes = []

    def __call__(self):
        self._document_pdb_module()
        self._output.start_classes()
        self._document_known_gimp_classes()
        self._document_unknown_gimp_classes()
        self._document_gimp_enums()
        self._document_gimpfu_constants()

    def _document_known_gimp_classes(self):
        gimp_classes = set([GIMP_TYPE_MAPPING[i] for i in KNOWN_GIMP_CLASSES])
        ordered_gimp_classes = self._get_ordered_gimp_classes()
        ordered_gimp_classes = [x for x in ordered_gimp_classes if x in gimp_classes]
        for gimp_class in ordered_gimp_classes:
            attrs = self._execute(
                'from pgimp.gimp.parameter import return_json\n' +
                'attrs = filter(lambda s: not s.startswith("__"), dir(gimp.{0:s}))\n'.format(gimp_class) +
                'props = filter(lambda a: type(eval("gimp.{:s}." + a)).__name__ == "getset_descriptor", attrs)\n'.format(gimp_class) +
                'methods = filter(lambda a: type(eval("gimp.{:s}." + a)).__name__ == "method_descriptor", attrs)\n'.format(gimp_class) +
                'baseclasses = map(lambda cls: cls.__name__, gimp.{0:s}.__bases__)\n'.format(gimp_class) +
                'return_json({"props": props, "methods": methods, "baseclasses": baseclasses})'
            )
            props = attrs['props']
            methods = attrs['methods']
            baseclasses = attrs['baseclasses']
            self._output.start_class(gimp_class, baseclasses)
            self._output.class_properties(props)
            self._output.class_methods(methods)

    def _get_ordered_gimp_classes(self):
        if not self._ordered_gimp_classes:
            unordered_gimp_classes = self._execute(textwrap.dedent(
                """
                import gimp
                from pgimp.gimp.parameter import return_json
                import inspect
                classes = inspect.getmembers(gimp, inspect.isclass)
                return_json(map(lambda cls: (cls[0], inspect.getmro(cls[1])[1].__name__), classes))
                """
            ))

            dependencies = {}
            for cls, parent in unordered_gimp_classes:
                if parent not in dependencies:
                    dependencies[parent] = []
                dependencies[parent].append(cls)
            visited = OrderedDict()
            to_visit = {'object'}
            while to_visit:
                to_visit_new = set([])
                for element in to_visit:
                    visited[element] = True
                    if element in dependencies:
                        to_visit_new = to_visit_new.union(set(dependencies[element]))
                to_visit = to_visit_new - set(visited)

            self._ordered_gimp_classes = list(visited.keys())
        return self._ordered_gimp_classes

    def _document_unknown_gimp_classes(self):
        gimp_classes = [GIMP_TYPE_MAPPING[i] for i in UNKNOWN_GIMP_CLASSES]
        ordered_gimp_classes = self._get_ordered_gimp_classes()
        ordered_gimp_classes = [x for x in ordered_gimp_classes if x in gimp_classes]
        for gimp_class in ordered_gimp_classes:
            self._output.start_unknown_class(gimp_class)

    def _document_pdb_module(self):
        self._output.start_module('pdb')
        pdb_dump = textwrap.dedent(
            """
            from collections import OrderedDict
            from pgimp.gimp.parameter import return_json

            result = OrderedDict()

            num_matches, procedure_names = pdb.gimp_procedural_db_query("", "", "", "", "", "", "")
            methods = sorted(procedure_names)
            for method in methods:
                blurb, help, author, copyright, date, proc_type, num_args, num_values = pdb.gimp_procedural_db_proc_info(method)
                result[method] = OrderedDict()
                result[method]['blurb'] = blurb
                result[method]['help'] = help
                result[method]['args'] = OrderedDict()
                result[method]['vals'] = OrderedDict()
                for arg_num in range(0, num_args):
                    arg_type, arg_name, arg_desc = pdb.gimp_procedural_db_proc_arg(method, arg_num)
                    if arg_name == 'run-mode':
                        continue
                    result[method]['args'][arg_name] = OrderedDict()
                    result[method]['args'][arg_name]['type'] = arg_type
                    result[method]['args'][arg_name]['desc'] = arg_desc
                for val_num in range(0, num_values):
                    val_type, val_name, val_desc = pdb.gimp_procedural_db_proc_val(method, val_num)
                    result[method]['vals'][val_name] = OrderedDict()
                    result[method]['vals'][val_name]['type'] = val_type
                    result[method]['vals'][val_name]['desc'] = val_desc

            return_json(result)
            """)
        methods = self._execute(pdb_dump, 20)
        for method in methods.keys():
            blurb = methods[method]['blurb']
            help = methods[method]['help']

            description = ''
            if blurb:
                description += blurb + '\n'
            if blurb and help:
                description += '\n'
            if help:
                description += help

            parameters = OrderedDict()
            for arg_name in methods[method]['args'].keys():
                arg_type = methods[method]['args'][arg_name]['type']
                arg_desc = methods[method]['args'][arg_name]['desc']
                parameters[arg_name] = (GIMP_TYPE_MAPPING[arg_type], arg_desc or '')

            return_values = OrderedDict()
            for val_name in methods[method]['vals'].keys():
                val_type = methods[method]['vals'][val_name]['type']
                val_desc = methods[method]['vals'][val_name]['desc']
                return_values[val_name] = (GIMP_TYPE_MAPPING[val_type], val_desc or '')

            self._output.method(method, description, parameters, return_values)

    def _execute(self, string: str, timeout_in_seconds: int = 10):
        return self._gsr.execute_and_parse_json(string, timeout_in_seconds=timeout_in_seconds)

    def _document_gimp_enums(self):
        enum_dump = textwrap.dedent(
            """
            import gimpenums
            from pgimp.gimp.parameter import return_json

            result = filter(lambda s: not s.startswith('__'), dir(gimpenums))
            result = zip(result, map(lambda s: eval('gimpenums.' + s), result))
            result = filter(lambda v: type(v[1]).__name__ != 'instance', result)

            return_json(result)
            """)
        enums = self._execute(enum_dump)
        self._output.gimpenums(enums)

    def _document_gimpfu_constants(self):
        const_dump = textwrap.dedent(
            """
            import gimpfu
            from pgimp.gimp.parameter import return_json

            result = filter(lambda s: not s.startswith('__') and s.isupper(), dir(gimpfu))
            result = zip(result, map(lambda s: eval('gimpfu.' + s), result))
            result = filter(lambda v: type(v[1]).__name__ not in ['instance', 'function'] , result)

            return_json(result)
            """)
        constants = self._execute(const_dump)
        self._output.gimpfu_constants(constants)


if __name__ == '__main__':
    import sys
    from pgimp.util import file
    sys.path.append(file.relative_to(__file__, '../../'))
    from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton

    generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
        file.relative_to(__file__, '../../gimp')
    ))
    generate_python_skeleton()
