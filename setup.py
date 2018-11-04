from setuptools import setup

from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton
from pgimp.util import file

setup(name='pgimp',
      version='1.0',
      description='Call gimp routines from python3 code.',
      url='https://github.com/mabu-github/pgimp',
      author='Mathias Burger',
      author_email='mathias.burger@gmail.com',
      license='MIT',
      packages=['pgimp'],
      zip_safe=False)

generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
   file.relative_to(__file__, 'gimp'))
)
generate_python_skeleton()
