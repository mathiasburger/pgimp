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
        assert os.path.exists(os.path.join(file.relative_to(__file__, '../../'), f))

    assert_file_exists('gimp/Channel.py')
    assert_file_exists('gimp/Color.py')
    assert_file_exists('gimp/ColorArray.py')
    assert_file_exists('gimp/Display.py')
    assert_file_exists('gimp/Drawable.py')
    assert_file_exists('gimp/Image.py')
    assert_file_exists('gimp/Item.py')
    assert_file_exists('gimp/Layer.py')
    assert_file_exists('gimp/Parasite.py')
    assert_file_exists('gimp/pdb.py')
    assert_file_exists('gimp/Selection.py')
    assert_file_exists('gimp/Status.py')
    assert_file_exists('gimp/Vectors.py')
    assert_file_exists('gimpenums/__init__.py')
