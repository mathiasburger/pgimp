import os
import re
import shutil
import subprocess


class GimpInstallationException(Exception):
    pass


if __name__ == '__main__':
    python = shutil.which('python2')
    if python is None:
        raise GimpInstallationException('Could not find a python2 installation.')
    proc = subprocess.Popen(
        [python],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    requirements = open(os.path.join(os.path.dirname(__file__), 'requirements-python2.txt'), 'r').readlines()
    imports = list(map(lambda r: re.split('[<=>\\s]', r)[0], filter(lambda x: x != '\n', requirements)))
    import_statements = list(map(lambda r: 'import ' + r, imports))
    stdout, stderr = proc.communicate(
        '\n'.join(import_statements).encode(),
        timeout=5
    )
    if stderr.decode() != '':
        raise GimpInstallationException(
            'At least one of the following packages is missing in the python2 installation: ' + ', '.join(imports)
        )
