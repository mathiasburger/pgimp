import os
import shutil
import subprocess

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

import pgimp
from pgimp import __version__, PROJECT, AUTHOR
from pgimp.util import file

PYTHON2_REQUIREMENTS = ['numpy', 'typing']


class GimpInstallationException(Exception):
    pass


def check_python2_installation():
    python = shutil.which('python2')
    if python is None:
        raise GimpInstallationException('Could not find a python2 installation.')
    proc = subprocess.Popen(
        [python],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    requirements = PYTHON2_REQUIREMENTS
    import_statements = list(map(lambda r: 'import ' + r, requirements))
    stdout, stderr = proc.communicate(
        '\n'.join(import_statements).encode(),
        timeout=5
    )
    if stderr.decode() != '':
        raise GimpInstallationException(
            'At least one of the following packages is missing in the python2 installation: ' + ', '.join(requirements)
        )


check_python2_installation()

pgimp.execute_scripts_with_process_check = False  # because psutil might not yet be installed


class GimpDocumentationGeneratorCommand(build_py):
    def run(self):
        if not self._dry_run:
            from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
            from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton

            generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
                file.relative_to(__file__, 'gimp')
            ))
            generate_python_skeleton()
            target_dir = self.build_lib
            shutil.copytree(file.relative_to(__file__, 'gimp'), os.path.join(target_dir, 'gimp'))
            shutil.copytree(file.relative_to(__file__, 'gimpenums'), os.path.join(target_dir, 'gimpenums'))
            shutil.copytree(file.relative_to(__file__, 'gimpfu'), os.path.join(target_dir, 'gimpfu'))
        return build_py.run(self)


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name=PROJECT,
    version=__version__,
    description='Interacting with gimp in python3.',
    url='https://github.com/mabu-github/pgimp',
    author=AUTHOR,
    author_email='mathias.burger@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    keywords='pgimp, gimp, annotating, annotation, machine-learning, graphics',
    packages=find_packages(),
    zip_safe=False,
    install_requires=list(filter(None, open('requirements.txt').read().split('\n'))),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    cmdclass=dict(
        build_py=GimpDocumentationGeneratorCommand
    ),
)
