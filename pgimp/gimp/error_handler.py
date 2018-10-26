import sys
import os


def __exception_hook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)
    sys.stderr.write('__GIMP_SCRIPT_ERROR__ {:d}'.format(1))
    pdb.gimp_quit(0)


sys.excepthook = __exception_hook
os.chdir(os.environ['__working_directory__'])
sys.path.append(os.getcwd())
