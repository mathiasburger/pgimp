# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import sys

import gimp


def __exception_hook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)
    sys.stderr.write('__GIMP_SCRIPT_ERROR__ {:d}'.format(1))
    gimp.pdb.gimp_quit(0)


sys.excepthook = __exception_hook
if '__working_directory__' in os.environ:
    os.chdir(os.environ['__working_directory__'])
sys.path.append(os.getcwd())
