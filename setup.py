from setuptools import setup, find_packages

from pgimp import __version__, project
from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton
from pgimp.util import file

generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
   file.relative_to(__file__, 'gimp'))
)
generate_python_skeleton()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name=project,
    version=__version__,
    description='Interacting with gimp in python3.',
    url='https://github.com/mabu-github/pgimp',
    author='Mathias Burger',
    author_email='mathias.burger@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_requires=list(filter(None, open('requirements.txt').read().split('\n'))),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
        "Operating System :: Mac OS",
    ],
)
