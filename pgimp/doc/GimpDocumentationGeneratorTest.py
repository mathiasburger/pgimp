import os

from pgimp.doc.GimpDocumentationGenerator import GimpDocumentationGenerator
from pgimp.doc.output.OutputPythonSkeleton import OutputPythonSkeleton
from pgimp.util import file


def test_generate_python_skeletons():
    generate_python_skeleton = GimpDocumentationGenerator(OutputPythonSkeleton(
        file.relative_to(__file__, '../../gimp'))
    )
    generate_python_skeleton()

    def assert_file_exists(f: str):
        assert os.path.exists(os.path.join(file.relative_to(__file__, '../../gimp'), f))

    assert_file_exists('Channel.py')
    assert_file_exists('Color.py')
    assert_file_exists('ColorArray.py')
    assert_file_exists('Display.py')
    assert_file_exists('Drawable.py')
    assert_file_exists('Image.py')
    assert_file_exists('Item.py')
    assert_file_exists('Layer.py')
    assert_file_exists('Parasite.py')
    assert_file_exists('pdb.py')
    assert_file_exists('Selection.py')
    assert_file_exists('Status.py')
    assert_file_exists('Vectors.py')
