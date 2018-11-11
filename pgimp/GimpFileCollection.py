import os
import textwrap
from glob import glob
from typing import List, Callable, Union, Dict

from pgimp.GimpException import GimpException
from pgimp.GimpFile import EXTENSION, GimpFile
from pgimp.GimpScriptRunner import GimpScriptRunner, JsonType
from pgimp.layers.Layer import Layer
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


class MissingFilesException(GimpException):
    """
    Indicates that files are missing.
    """
    pass


class GimpFileCollection:
    def __init__(self, files: List[str], gimp_file_factory=lambda file: GimpFile(file)) -> None:
        super().__init__()
        self._files = files
        self._gimp_file_factory = gimp_file_factory
        self._gsr = GimpScriptRunner()

    def get_files(self) -> List[str]:
        """
        Returns the list of files contained in the collection.

        :return: List of files contained in the collection
        """
        return self._files

    def get_prefix(self) -> str:
        """
        Returns the common path prefix for all files including a trailing slash.

        :return: Common path prefix for all files including a trailing slash.
        """
        if len(self._files) == 0:
            return ''
        if len(self._files) == 1:
            return os.path.dirname(self._files[0]) + '/'
        commonprefix = os.path.commonprefix(self._files)
        if os.path.isdir(commonprefix):
            return commonprefix
        return os.path.dirname(commonprefix) + '/'

    def replace_prefix(self, prefix: str, new_prefix: str='') -> 'GimpFileCollection':
        """
        Returns a new collection with filenames that do not contain the prefix.

        :param prefix: The prefix to strip away.
        :param new_prefix: The replacement value for the prefix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` where file prefixes are stripped away.
        """
        return self.replace_path_components(prefix=prefix, new_prefix=new_prefix)

    def replace_suffix(self, suffix: str, new_suffix: str='') -> 'GimpFileCollection':
        """
        Returns a new collection with filenames that do not contain the suffix.

        :param suffix: The suffix to strip away.
        :param new_suffix: The replacement value for the suffix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` where file suffixed are stripped away.
        """
        return self.replace_path_components(suffix=suffix, new_suffix=new_suffix)

    def replace_path_components(self, prefix: str = '', new_prefix: str = '', suffix: str = '', new_suffix: str = '') -> 'GimpFileCollection':
        """
        Returns a new collection with replaced path components.

        :param prefix: The prefix to replace.
        :param suffix: The suffix to replace.
        :param new_prefix: The replacement value for the prefix.
        :param new_suffix: The replacement value for the suffix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` where the given path components
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
        """
        Find files that contain a layer matching the predicate.

        :param predicate: A function that takes a list of layers and returns bool.
        :return: List of files matching the predicate.
        """
        return list(filter(lambda file: predicate(self._gimp_file_factory(file).layers()), self._files))

    def find_files_containing_layer_by_name(self, layer_name: str, timeout_in_seconds: float=None) -> List[str]:
        """
        Find files that contain a layer that matching the given name.

        :param layer_name: Layer name to search for.
        :param timeout_in_seconds: Script execution timeout in seconds.
        :return: List of files containing the layer with the given name.
        """
        return self.find_files_by_script(textwrap.dedent(
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
        ).format(escape_single_quotes(layer_name)), timeout_in_seconds=timeout_in_seconds)

    def find_files_by_script(self, script_predicate: str, timeout_in_seconds: float=None) -> List[str]:
        """
        Find files matching certain criteria by executing a gimp script.

        If the script opens a file with **open_xcf('__file__')**, then the script is executed for each file
        and a boolean result returned by **return_bool(value)** is expected.

        If the script retrieves the whole list of files with **get_json('__files__')**, then the script is
        only executed once and passed the whole list of files as a parameter. A result returned by
        **return_json(value)** in the form of a list is expected. This solution has better performance
        but you need to make sure that memory is cleaned up between opening files, e.g. by invoking
        **gimp_image_delete(image)**.

        :param script_predicate: Script to be executed.
        :param timeout_in_seconds: Script execution timeout in seconds.
        :return: List of files matching the criteria.
        """
        if "open_xcf('__file__')" in script_predicate and "return_bool(" in script_predicate:
            return list(filter(lambda file: self._gsr.execute_and_parse_bool(
                script_predicate.replace('__file__', escape_single_quotes(file)),
                timeout_in_seconds=timeout_in_seconds
            ), self._files))
        elif "get_json('__files__')" in script_predicate and "return_json(" in script_predicate:
            return self._gsr.execute_and_parse_json(
                script_predicate,
                parameters={'__files__': self._files},
                timeout_in_seconds=timeout_in_seconds
            )
        else:
            raise GimpMissingRequiredParameterException(
                'Either an image file must be opened with open_xcf(\'__file__\') ' +
                'and the result is returned with return_bool() ' +
                'or a list of files must be retrieved by get_json(\'__files__\') ' +
                'and the result is returned with return_json().'
            )

    def execute_script_and_return_json(self, script: str, parameters: dict=None, timeout_in_seconds: float=None) -> Union[JsonType, Dict[str, JsonType]]:
        """
        Execute a gimp script on the collection.

        If the script opens a file with **open_xcf('__file__')**, then the script is executed for each file
        and a result returned by **return_json(value)** is expected. The results will be returned as a
        dictionary containing the filenames as keys and the results as values.

        If the script retrieves the whole list of files with **get_json('__files__')**, then the script is
        only executed once and passed the whole list of files as a parameter. A result returned by
        **return_json(value)** is expected. This solution has better performance
        but you need to make sure that memory is cleaned up between opening files, e.g. by invoking
        **gimp_image_delete(image)**.

        :param script: Script to be executed on the files.
        :param parameters: Parameters to pass to the script.
        :param timeout_in_seconds:  Script execution timeout in seconds.
        :return: Dictionary of filenames and results if the script reads a single file.
                 Json if the script takes the whole list of files.
        """
        parameters = parameters or {}
        if "open_xcf('__file__')" in script and "return_json(" in script:
            return {file: self._gsr.execute_and_parse_json(
                script.replace('__file__', escape_single_quotes(file)),
                parameters=parameters,
                timeout_in_seconds=timeout_in_seconds
            ) for file in self._files}
        elif "get_json('__files__')" in script and "return_json(" in script:
            return self._gsr.execute_and_parse_json(
                script,
                parameters={**parameters, '__files__': self._files},
                timeout_in_seconds=timeout_in_seconds
            )
        else:
            raise GimpMissingRequiredParameterException(
                'Either an image file must be opened with open_xcf(\'__file__\') ' +
                'and the result is returned with return_json() ' +
                'or a list of files must be retrieved by get_json(\'__files__\') ' +
                'and the result is returned with return_json().'
            )

    def copy_layer_from(self, other_collection: 'GimpFileCollection', layer_name: str, layer_position: int=1, timeout_in_seconds: float=None) -> 'GimpFileCollection':
        """
        Copies a layer from another collection into this collection.

        :param other_collection: The collection from which to take the layer.
        :param layer_name: Name of the layer to copy.
        :param layer_position: Layer position in the destination image.
        :return: :py:class:`~pgimp.GimpFileCollection.GimpFileCollection`
        """
        prefix_in_other_collection = other_collection.get_prefix()
        files_in_other_collection = map(lambda file: file[len(prefix_in_other_collection):], other_collection._files)
        prefix_in_this_collection = self.get_prefix()
        files_in_this_collection = map(lambda file: file[len(prefix_in_this_collection):], other_collection._files)
        missing = set(files_in_this_collection) - set(files_in_other_collection)
        if len(missing) > 0:
            raise MissingFilesException(
                'The other collection is smaller than this collection by the following entries: ' +
                ', '.join(missing)
            )

        script = textwrap.dedent(
            """
            import gimp
            import os
            from pgimp.gimp.file import open_xcf, save_xcf
            from pgimp.gimp.parameter import get_json, get_string, get_int, return_json
            from pgimp.gimp.layer import copy_layer
            
            prefix_in_other_collection = get_string('prefix_in_other_collection')
            prefix_in_this_collection = get_string('prefix_in_this_collection')
            layer_name = get_string('layer_name')
            layer_position = get_int('layer_position')
            files = get_json('__files__')
            
            for file in files:
                file = file[len(prefix_in_this_collection):]
                file_src = os.path.join(prefix_in_other_collection, file)
                file_dst = os.path.join(prefix_in_this_collection, file)
                image_src = open_xcf(file_src)
                image_dst = open_xcf(file_dst)
                copy_layer(image_src, layer_name, image_dst, layer_name, layer_position)
                save_xcf(image_dst, file_dst)
                gimp.pdb.gimp_image_delete(image_src)
                gimp.pdb.gimp_image_delete(image_dst)
                
            return_json(None)
            """
        )

        self.execute_script_and_return_json(
            script,
            parameters={
                'prefix_in_other_collection': prefix_in_other_collection,
                'prefix_in_this_collection': prefix_in_this_collection,
                'layer_name': layer_name,
                'layer_position': layer_position,
            },
            timeout_in_seconds=timeout_in_seconds
        )
        return self

    @classmethod
    def create_from_pathname(cls, pathname: str):
        """
        Create a collection of gimp files by pathname.

        :param pathname: Can be a file with or without .xcf suffix, directory or recursive directory search.
                         Allowed wildcards include '*' for matching zero or more characters
                         and '**' for recursive search.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` that contains an ordered list of filenames.
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
