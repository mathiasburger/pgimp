from setuptools import setup, find_packages

from pgimp import __version__, project
from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton
from pgimp.util import file

generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
   file.relative_to(__file__, 'gimp'))
)
generate_python_skeleton()

setup(
    name=project,
    version=__version__,
    description='Call gimp routines from python3 code.',
    url='https://github.com/mabu-github/pgimp',
    author='Mathias Burger',
    author_email='mathias.burger@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_requires=list(filter(None, open('requirements.txt').read().split('\n')))
)
