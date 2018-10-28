from collections import OrderedDict

from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.documentation.output.Output import Output

gimpTypeMapping = {
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
See also gimp-procedural-db-proc-arg documentation.
"""


class GimpDocumentationGenerator:
    def __init__(self, output: Output) -> None:
        super().__init__()
        self._output = output
        self._gsr: GimpScriptRunner = GimpScriptRunner()

    def __call__(self):
        module = 'pdb'
        self._output.start_module(module)
        methods = self._execute(
            'num_matches, procedure_names = pdb.gimp_procedural_db_query("", "", "", "", "", "", "")\n' +
            'return_json(procedure_names)'
        )
        methods = sorted(methods)
        for method in methods:
            blurb, help, num_args, num_values = self._execute(
                'blurb, help, author, copyright, date, proc_type, num_args, num_values = \\\n' +
                '    pdb.gimp_procedural_db_proc_info("{:s}")\n'.format(method) +
                'return_json([blurb, help, num_args, num_values])'
            )

            description = ''
            if blurb:
                description += blurb + '\n'
            if blurb and help:
                description += '\n'
            if help:
                description += help

            parameters = OrderedDict()
            for arg_num in range(0, num_args):
                arg_type, arg_name, arg_desc = self._execute(
                    'arg_type, arg_name, arg_desc = pdb.gimp_procedural_db_proc_arg("{:s}", {:d})\n'.format(
                        method,
                        arg_num
                    ) + 'return_json([arg_type, arg_name, arg_desc])'
                )
                parameters[arg_name] = (gimpTypeMapping[arg_type], arg_desc or '')

            return_values = OrderedDict()
            for val_num in range(0, num_values):
                val_type, val_name, val_desc = self._execute(
                    'val_type, val_name, val_desc = pdb.gimp_procedural_db_proc_val("{:s}", {:d})\n'.format(
                        method, val_num
                    ) + 'return_json([val_type, val_name, val_desc])'
                )
                return_values[val_name] = (gimpTypeMapping[val_type], val_desc or '')
            
            self._output.method(method, description, parameters, return_values)

    def _execute(self, string: str):
        return self._gsr.execute_and_parse_json(string, timeout_in_seconds=3)
