import textwrap

import numpy as np
import pytest

from pgimp.GimpFile import GimpFile
from pgimp.GimpFileCollection import GimpFileCollection, NonExistingPathComponentException, \
    GimpMissingRequiredParameterException
from pgimp.util import file
from pgimp.util.TempFile import TempFile
from pgimp.util.string import escape_single_quotes


def test_create_from_pathname_with_file():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/first'))
    assert len(collection.get_files()) == 1

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/first.xcf'))
    assert len(collection.get_files()) == 1

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/first.png'))
    assert len(collection.get_files()) == 0


def test_create_from_pathname_with_directory():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files'))
    assert len(collection.get_files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/'))
    assert len(collection.get_files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/*'))
    assert len(collection.get_files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/*.xcf'))
    assert len(collection.get_files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/*.png'))
    assert len(collection.get_files()) == 0


def test_create_from_pathname_with_recursive_match():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))
    assert len(collection.get_files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/'))
    assert len(collection.get_files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/*'))
    assert len(collection.get_files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/*.xcf'))
    assert len(collection.get_files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/*.png'))
    assert len(collection.get_files()) == 0


def test_ordering():
    prefix = file.relative_to(__file__, 'test-resources/files/')
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))
    collection = collection.replace_prefix(prefix)
    assert [
               'first.xcf',
               'second.xcf',
               'a/third.xcf',
               'a/b/fourth.xcf',
           ] == collection.get_files()


def test_replace_path_components():
    prefix = file.relative_to(__file__, 'test-resources/files/')
    suffix = '.xcf'
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))

    collection = collection.replace_path_components(prefix, '#', suffix, '%')

    assert [
               '#first%',
               '#second%',
               '#a/third%',
               '#a/b/fourth%',
           ] == collection.get_files()


def test_replace_path_components_with_non_existing_component():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))

    with pytest.raises(NonExistingPathComponentException):
        collection.replace_path_components('wrong_prefix', '#')


def test_replace_path_components_without_replacements():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))

    files_before = collection.get_files()
    collection = collection.replace_path_components()
    files_after = collection.get_files()

    assert files_before == files_after


def test_find_files_containing_layer_by_predictate():
    with TempFile('.xcf') as with_white, TempFile('.xcf') as without_white:
        GimpFile(with_white)\
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8))\
            .add_layer_from_numpy('White', np.ones(shape=(1, 1)))

        GimpFile(without_white) \
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \
            .add_layer_from_numpy('Black', np.zeros(shape=(1, 1)))

        collection = GimpFileCollection([with_white, without_white])

        files = collection.find_files_containing_layer_by_predictate(
            lambda layers: 'White' in map(lambda layer: layer.name, layers)
        )
        assert len(files) == 1
        assert with_white == files[0]

        files = collection.find_files_containing_layer_by_predictate(
            lambda layers: 'Not existing' in map(lambda layer: layer.name, layers)
        )
        assert len(files) == 0


def test_find_files_containing_layer_by_name():
    with TempFile('.xcf') as with_white, TempFile('.xcf') as without_white:
        GimpFile(with_white)\
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8))\
            .add_layer_from_numpy('White', np.ones(shape=(1, 1)))

        GimpFile(without_white) \
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \
            .add_layer_from_numpy('Black', np.zeros(shape=(1, 1)))

        collection = GimpFileCollection([with_white, without_white])

        files = collection.find_files_containing_layer_by_name('White', timeout_in_seconds=10)
        assert len(files) == 1
        assert with_white == files[0]

        files = collection.find_files_containing_layer_by_name('Not existing', timeout_in_seconds=10)
        assert len(files) == 0


def test_find_files_by_script_with_script_that_takes_single_file():
    with TempFile('.xcf') as with_white, TempFile('.xcf') as without_white:
        GimpFile(with_white)\
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8))\
            .add_layer_from_numpy('White', np.ones(shape=(1, 1)))

        GimpFile(without_white) \
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \
            .add_layer_from_numpy('Black', np.zeros(shape=(1, 1)))

        collection = GimpFileCollection([with_white, without_white])

        script = textwrap.dedent(
            """
            from pgimp.gimp.file import open_xcf
            from pgimp.gimp.parameter import return_bool
            image = open_xcf('__file__')
            for layer in image.layers:
                if layer.name == '{0:s}':
                    return_bool(True)
            return_bool(False)
            """
        )

        files = collection.find_files_by_script(script.format(escape_single_quotes('White')), timeout_in_seconds=3)
        assert len(files) == 1
        assert with_white == files[0]

        files = collection.find_files_by_script(script.format(escape_single_quotes('Not existing')), timeout_in_seconds=3)
        assert len(files) == 0


def test_find_files_by_script_with_script_that_takes_multiple_files():
    with TempFile('.xcf') as with_white, TempFile('.xcf') as without_white:
        GimpFile(with_white)\
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8))\
            .add_layer_from_numpy('White', np.ones(shape=(1, 1)))

        GimpFile(without_white) \
            .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \
            .add_layer_from_numpy('Black', np.zeros(shape=(1, 1)))

        collection = GimpFileCollection([with_white, without_white])

        script = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.file import open_xcf
            from pgimp.gimp.parameter import return_json, get_json
            files = get_json('__files__')
            matches = []
            for file in files:
                image = open_xcf(file)
                for layer in image.layers:
                    if layer.name == '{0:s}':
                        matches.append(file)
                gimp.pdb.gimp_image_delete(image)
            return_json(matches)
            """
        )

        files = collection.find_files_by_script(script.format(escape_single_quotes('White')), timeout_in_seconds=3)
        assert len(files) == 1
        assert with_white == files[0]

        files = collection.find_files_by_script(script.format(escape_single_quotes('Not existing')), timeout_in_seconds=3)
        assert len(files) == 0


def test_find_files_by_script_without_required_parameters():
    collection = GimpFileCollection([])
    script = textwrap.dedent(
        """
        print(1)
        """
    )

    with pytest.raises(GimpMissingRequiredParameterException):
        collection.find_files_by_script(script, timeout_in_seconds=3)
