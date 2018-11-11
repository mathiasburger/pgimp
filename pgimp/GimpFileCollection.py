import os
from glob import glob
from typing import List

from pgimp.GimpException import GimpException
from pgimp.GimpFile import EXTENSION


class NonExistingPathComponentException(GimpException):
    pass


class GimpFileCollection:
    def __init__(self, files: List[str]) -> None:
        super().__init__()
        self._files = files

    def files(self):
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
