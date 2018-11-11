import os
from glob import glob
from typing import List, Callable

from gimp.Layer import Layer
from pgimp.GimpException import GimpException
from pgimp.GimpFile import EXTENSION, GimpFile
from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.util.string import escape_single_quotes


class NonExistingPathComponentException(GimpException):
    """
    Indicates that a path should have had a specific component, e.g. prefix or suffix.
    """
    pass


class GimpMissingRequiredParameterException(GimpException):
    """
    Indicates that a parameter that is necessary for a gimp script is missing.
    """
    pass


class GimpFileCollection:
    def __init__(self, files: List[str], gimp_file_factory=lambda file: GimpFile(file)) -> None:
        super().__init__()
        self._files = files
        self._gimp_file_factory = gimp_file_factory
        self._gsr = GimpScriptRunner()

    def get_files(self):
        return self._files

    def replace_prefix(self, prefix: str, new_prefix: str='') -> 'GimpFileCollection':
        """
        Returns a new collection with filenames that do not contain the prefix.

        :param prefix: The prefix to strip away.
        :param new_prefix: The replacement value for the prefix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection' where file prefixes are stripped away.
        """
        return self.replace_path_components(prefix=prefix, new_prefix=new_prefix)

    def replace_suffix(self, suffix: str, new_suffix: str='') -> 'GimpFileCollection':
        """
        Returns a new collection with filenames that do not contain the suffix.

        :param suffix: The suffix to strip away.
        :param new_suffix: The replacement value for the suffix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection' where file suffixed are stripped away.
        """
        return self.replace_path_components(suffix=suffix, new_suffix=new_suffix)

    def replace_path_components(self, prefix: str = '', new_prefix: str = '', suffix: str = '', new_suffix: str = '') -> 'GimpFileCollection':
        """
        Returns a new collection with replaced path components.

        :param prefix: The prefix to replace.
        :param suffix: The suffix to replace.
        :param new_prefix: The replacement value for the prefix.
        :param new_suffix: The replacement value for the suffix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection' where the given path components
                 are replaced.
        """
        files = self._files
        check = list(filter(lambda file: file.startswith(prefix) and file.endswith(suffix), files))
        if len(check) != len(files):
            raise NonExistingPathComponentException('All files must start with the given prefix and end with the given suffix.')
        prefix_length = len(prefix)
        files = list(map(lambda file: new_prefix + file[prefix_length:], files))
        suffix_length = len(suffix)
        if suffix_length > 0:
            files = map(lambda file: file[:-suffix_length] + new_suffix, files)
        return GimpFileCollection(list(files))

    def find_files_containing_layer_by_predictate(self, predicate: Callable[[List[Layer]], bool]) -> List[str]:
        return list(filter(lambda file: predicate(self._gimp_file_factory(file).layers()), self._files))

    def find_files_containing_layer_by_name(self, layer_name: str):
        return self.find_files_containing_layer_by_predictate(
            lambda layers: layer_name in map(lambda layer: layer.name, layers)
        )

    def find_files_by_script(self, script_predicate: str, timeout_in_seconds: float=None) -> List[str]:
        if "open_xcf('__file__')" in script_predicate:
            return list(filter(lambda file: self._gsr.execute_and_parse_bool(
                script_predicate.replace('__file__', escape_single_quotes(file)),
                timeout_in_seconds=timeout_in_seconds
            ), self._files))
        elif "get_json('__files__')" in script_predicate:
            return self._gsr.execute_and_parse_json(
                script_predicate,
                parameters={'__files__': self._files},
                timeout_in_seconds=timeout_in_seconds
            )
        else:
            raise GimpMissingRequiredParameterException(
                'Either an image file must be opened with open_xcf(\'__file__\') ' +
                'or a list of files must be retrieved by get_json(\'__files__\').'
            )

    @classmethod
    def create_from_pathname(cls, pathname: str):
        """
        Create a collection of gimp files by pathname.

        :param pathname: Can be a file with or without .xcf suffix, directory or recursive directory search.
                         Allowed wildcards include '*' for matching zero or more characters
                         and '**' for recursive search.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection' that contains an ordered list of filenames.
        """
        if pathname.endswith('**') or pathname.endswith('**/'):
            pathname = os.path.join(pathname, '*' + EXTENSION)
        elif os.path.isdir(pathname):  # only search for gimp files in dir
            pathname = os.path.join(pathname, '*' + EXTENSION)
        else:  # only search for gimp files and add extension if necessary
            base, extension = os.path.splitext(pathname)
            if extension != EXTENSION and extension != '':
                return cls([])
            pathname = base + EXTENSION

        files = glob(pathname, recursive=True)
        files = sorted(files, key=lambda file: (file.count('/'), file))
        return cls(list(files))
