import pytest

from pgimp.GimpFileCollection import GimpFileCollection, NonExistingPathComponentException
from pgimp.util import file


def test_create_from_pathname_with_file():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/first'))
    assert len(collection.files()) == 1

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/first.xcf'))
    assert len(collection.files()) == 1

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/first.png'))
    assert len(collection.files()) == 0


def test_create_from_pathname_with_directory():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files'))
    assert len(collection.files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/'))
    assert len(collection.files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/*'))
    assert len(collection.files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/*.xcf'))
    assert len(collection.files()) == 2

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/*.png'))
    assert len(collection.files()) == 0


def test_create_from_pathname_with_recursive_match():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))
    assert len(collection.files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/'))
    assert len(collection.files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/*'))
    assert len(collection.files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/*.xcf'))
    assert len(collection.files()) == 4

    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**/*.png'))
    assert len(collection.files()) == 0


def test_ordering():
    prefix = file.relative_to(__file__, 'test-resources/files/')
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))
    collection = collection.replace_prefix(prefix)
    assert [
               'first.xcf',
               'second.xcf',
               'a/third.xcf',
               'a/b/fourth.xcf',
           ] == collection.files()


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
           ] == collection.files()


def test_replace_path_components_with_non_existing_component():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))

    with pytest.raises(NonExistingPathComponentException):
        collection.replace_path_components('wrong_prefix', '#')


def test_replace_path_components_without_replacements():
    collection = GimpFileCollection.create_from_pathname(file.relative_to(__file__, 'test-resources/files/**'))

    files_before = collection.files()
    collection = collection.replace_path_components()
    files_after = collection.files()

    assert files_before == files_after
