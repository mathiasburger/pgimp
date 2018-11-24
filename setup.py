from setuptools import setup, find_packages
from setuptools.command.install import install

from pgimp import __version__, project, author
from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton
from pgimp.util import file


class GimpDocumentationGeneratorCommand(install):
    def run(self):
        if not self._dry_run:
            generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
                file.relative_to(__file__, 'gimp'))
            )
            generate_python_skeleton()
        return install.run(self)


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name=project,
    version=__version__,
    description='Interacting with gimp in python3.',
    url='https://github.com/mabu-github/pgimp',
    author=author,
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
        install=GimpDocumentationGeneratorCommand
    ),
)
