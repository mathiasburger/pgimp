# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import sys

import gimp

binary = bool(os.environ['__binary__'])
stdout_file = os.environ['__stdout__']
sys.stdout = open(stdout_file, 'w' if not binary else 'wb')
stderr_file = os.environ['__stderr__']
sys.stderr = open(stderr_file, 'w')


def __exception_hook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)
    sys.stderr.write('__GIMP_SCRIPT_ERROR__ {:d}'.format(1))
    gimp.pdb.gimp_quit(0)


sys.excepthook = __exception_hook
if '__working_directory__' in os.environ:
    os.chdir(os.environ['__working_directory__'])
sys.path.append(os.getcwd())

if '__PYTHONPATH__' in os.environ:
    pythonpath = os.environ['__PYTHONPATH__']
    for path_component in [x.strip() for x in pythonpath.split(':')]:
        sys.path.append(path_component)
