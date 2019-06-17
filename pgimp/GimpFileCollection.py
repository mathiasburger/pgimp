# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import textwrap
from enum import Enum
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


class GimpMissingRequiredParameterException(GimpException):
    """
    Indicates that a parameter that is necessary for a gimp script is missing.
    """


class MissingFilesException(GimpException):
    """
    Indicates that files are missing.
    """


class MaskForegroundColor(Enum):
    WHITE = 1
    BLACK = 0


class GimpFileCollection:
    def __init__(self, files: List[str], gimp_file_factory=lambda file: GimpFile(file)) -> None:
        super().__init__()
        self._files = files
        self._gimp_file_factory = gimp_file_factory
        self._gsr = GimpScriptRunner()

    def get_files(self) -> List[str]:
        """
        Returns the list of files contained in the collection.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> gfc = GimpFileCollection(['a.xcf', 'b.xcf'])
        >>> gfc.get_files()
        ['a.xcf', 'b.xcf']

        :return: List of files contained in the collection
        """
        return self._files

    def get_prefix(self) -> str:
        """
        Returns the common path prefix for all files including a trailing slash.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> gfc = GimpFileCollection(['common/pre/dir/a.xcf', 'common/pre/files/b.xcf'])
        >>> gfc.get_prefix()
        'common/pre/'

        :return: Common path prefix for all files including a trailing slash.
        """
        if not self._files:
            return ''
        if len(self._files) == 1:
            return os.path.dirname(self._files[0]) + '/'
        commonprefix = os.path.commonprefix(self._files)
        if os.path.isdir(commonprefix):
            return commonprefix
        return os.path.dirname(commonprefix) + '/'

    def replace_prefix(self, prefix: str, new_prefix: str = '') -> 'GimpFileCollection':
        """
        Returns a new collection with filenames where the old prefix is replaced by a new prefix.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> gfc = GimpFileCollection(['common/pre/dir/a.xcf', 'common/pre/files/b.xcf'])
        >>> gfc.replace_prefix('common/pre', 'newpre').get_files()
        ['newpre/dir/a.xcf', 'newpre/files/b.xcf']

        :param prefix: The prefix to strip away.
        :param new_prefix: The replacement value for the prefix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` where file prefixes are stripped away.
        """
        return self.replace_path_components(prefix=prefix, new_prefix=new_prefix)

    def replace_suffix(self, suffix: str, new_suffix: str = '') -> 'GimpFileCollection':
        """
        Returns a new collection with filenames that do not contain the suffix.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> gfc = GimpFileCollection(['dir/a_tmp.xcf', 'files/b_tmp.xcf'])
        >>> gfc.replace_suffix('tmp', 'final').get_files()
        ['dir/a_final.xcf', 'files/b_final.xcf']

        :param suffix: The suffix to strip away.
        :param new_suffix: The replacement value for the suffix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` where file suffixed are stripped away.
        """
        return self.replace_path_components(suffix=suffix, new_suffix=new_suffix)

    def replace_path_components(
            self,
            prefix: str = '',
            new_prefix: str = '',
            suffix: str = '',
            new_suffix: str = ''
    ) -> 'GimpFileCollection':
        """
        Returns a new collection with replaced path components.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> gfc = GimpFileCollection(['pre/filepre_a_suf.xcf', 'pre/filepre_b_suf.xcf'])
        >>> gfc.replace_path_components(prefix='pre/filepre_', new_prefix='', suffix='_suf', new_suffix='').get_files()
        ['a.xcf', 'b.xcf']

        :param prefix: The prefix to replace.
        :param suffix: The suffix to replace.
        :param new_prefix: The replacement value for the prefix.
        :param new_suffix: The replacement value for the suffix.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` where the given path components
                 are replaced.
        """
        files = self._files
        if not suffix.endswith(EXTENSION):
            suffix += EXTENSION
        if not new_suffix.endswith(EXTENSION):
            new_suffix += EXTENSION
        check = list(filter(lambda file: file.startswith(prefix) and file.endswith(suffix), files))
        if len(check) != len(files):
            raise NonExistingPathComponentException(
                'All files must start with the given prefix and end with the given suffix.'
            )

        prefix_length = len(prefix)
        files = list(map(lambda file: new_prefix + file[prefix_length:], files))

        suffix_length = len(suffix)
        files = map(lambda file: file[:-suffix_length] + new_suffix, files)
        return GimpFileCollection(list(files))

    def find_files_containing_layer_by_predictate(self, predicate: Callable[[List[Layer]], bool]) -> List[str]:
        """
        Find files that contain a layer matching the predicate.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     def find_foreground(layers: List[Layer]):
        ...         return list(filter(lambda layer: layer.name == 'Foreground', layers)) != []
        ...     gfc.find_files_containing_layer_by_predictate(find_foreground)
        ['..._fg.xcf']

        :param predicate: A function that takes a list of layers and returns bool.
        :return: List of files matching the predicate.
        """
        return list(filter(lambda file: predicate(self._gimp_file_factory(file).layers()), self._files))

    def find_files_containing_layer_by_name(self, layer_name: str, timeout_in_seconds: float = None) -> List[str]:
        """
        Find files that contain a layer that matching the given name.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     gfc.find_files_containing_layer_by_name('Foreground')
        ['..._fg.xcf']

        :param layer_name: Layer name to search for.
        :param timeout_in_seconds: Script execution timeout in seconds.
        :return: List of files containing the layer with the given name.
        """
        return self.find_files_by_script(textwrap.dedent(
            """
            from pgimp.gimp.parameter import return_json, get_json
            from pgimp.gimp.file import XcfFile
            files = get_json('__files__')
            matches = []
            for file in files:
                with XcfFile(file) as image:
                    for layer in image.layers:
                        if layer.name == '{0:s}':
                            matches.append(file)
            return_json(matches)
            """
        ).format(escape_single_quotes(layer_name)), timeout_in_seconds=timeout_in_seconds)

    def find_files_by_script(self, script_predicate: str, timeout_in_seconds: float = None) -> List[str]:
        """
        Find files matching certain criteria by executing a gimp script.

        If the script opens a file with **open_xcf('__file__')**, then the script is executed for each file
        and a boolean result returned by **return_bool(value)** is expected.

        If the script retrieves the whole list of files with **get_json('__files__')**, then the script is
        only executed once and passed the whole list of files as a parameter. A result returned by
        **return_json(value)** in the form of a list is expected. This solution has better performance
        but you need to make sure that memory is cleaned up between opening files, e.g. by invoking
        **gimp_image_delete(image)**.

        Example with script that is executed per file:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.util.string import escape_single_quotes
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     script = textwrap.dedent(
        ...         '''
        ...         from pgimp.gimp.file import open_xcf
        ...         from pgimp.gimp.parameter import return_bool
        ...         image = open_xcf('__file__')
        ...         for layer in image.layers:
        ...             if layer.name == '{0:s}':
        ...                 return_bool(True)
        ...         return_bool(False)
        ...         '''
        ...     ).format(escape_single_quotes('Foreground'))
        ...     gfc.find_files_by_script(script)
        ['..._fg.xcf']

        Example with script that is executed once on all files:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.util.string import escape_single_quotes
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     script = textwrap.dedent(
        ...         '''
        ...         import gimp
        ...         from pgimp.gimp.file import XcfFile
        ...         from pgimp.gimp.parameter import return_json, get_json
        ...         files = get_json('__files__')
        ...         matches = []
        ...         for file in files:
        ...             with XcfFile(file) as image:
        ...                 for layer in image.layers:
        ...                     if layer.name == '{0:s}':
        ...                         matches.append(file)
        ...         return_json(matches)
        ...         '''
        ...     ).format(escape_single_quotes('Foreground'))
        ...     gfc.find_files_by_script(script)
        ['..._fg.xcf']

        :param script_predicate: Script to be executed.
        :param timeout_in_seconds: Script execution timeout in seconds.
        :return: List of files matching the criteria.
        """
        if "open_xcf('__file__')" in script_predicate and "return_bool(" in script_predicate:
            return list(filter(lambda file: self._gsr.execute_and_parse_bool(
                script_predicate.replace('__file__', escape_single_quotes(file)),
                timeout_in_seconds=timeout_in_seconds
            ), self._files))
        if "get_json('__files__')" in script_predicate and "return_json(" in script_predicate:
            return self._gsr.execute_and_parse_json(
                script_predicate,
                parameters={'__files__': self._files},
                timeout_in_seconds=timeout_in_seconds
            )
        raise GimpMissingRequiredParameterException(
            'Either an image file must be opened with open_xcf(\'__file__\') ' +
            'and the result is returned with return_bool() ' +
            'or a list of files must be retrieved by get_json(\'__files__\') ' +
            'and the result is returned with return_json().'
        )

    def execute_script_and_return_json(
            self,
            script: str,
            parameters: dict = None,
            timeout_in_seconds: float = None
    ) -> Union[JsonType, Dict[str, JsonType]]:
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

        Example with script that is executed per file:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.util.string import escape_single_quotes
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     script = textwrap.dedent(
        ...         '''
        ...         from pgimp.gimp.file import open_xcf
        ...         from pgimp.gimp.parameter import return_json
        ...         image = open_xcf('__file__')
        ...         for layer in image.layers:
        ...             if layer.name == '{0:s}':
        ...                 return_json(True)
        ...         return_json(False)
        ...         '''
        ...     ).format(escape_single_quotes('Foreground'))
        ...     gfc.execute_script_and_return_json(script)
        {'..._bg.xcf': False, '..._fg.xcf': True}

        Example with script that is executed once on all files using open_xcf():

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.util.string import escape_single_quotes
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     script = textwrap.dedent(
        ...         '''
        ...         import gimp
        ...         from pgimp.gimp.file import XcfFile
        ...         from pgimp.gimp.parameter import return_json, get_json
        ...         files = get_json('__files__')
        ...         matches = []
        ...         for file in files:
        ...             with XcfFile(file) as image:
        ...                 for layer in image.layers:
        ...                     if layer.name == '{0:s}':
        ...                         matches.append(file)
        ...         return_json(matches)
        ...         '''
        ...     ).format(escape_single_quotes('Foreground'))
        ...     gfc.execute_script_and_return_json(script)
        ['..._fg.xcf']

        Example with script that is executed once on all files using for_each_file():

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.util.string import escape_single_quotes
        >>> import numpy as np
        >>> with TempFile('_bg.xcf') as f1, TempFile('_fg.xcf') as f2:  # doctest: +ELLIPSIS
        ...     gf1 = GimpFile(f1).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(f2).create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     script = textwrap.dedent(
        ...         '''
        ...         from pgimp.gimp.file import for_each_file
        ...         from pgimp.gimp.parameter import return_json, get_json
        ...
        ...         matches = []
        ...
        ...         def layer_matches(image, file):
        ...             for layer in image.layers:
        ...                 if layer.name == '{0:s}':
        ...                     matches.append(file)
        ...
        ...         for_each_file(layer_matches)
        ...         return_json(matches)
        ...         '''
        ...     ).format(escape_single_quotes('Foreground'))
        ...     gfc.execute_script_and_return_json(script)
        ['..._fg.xcf']

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
        elif ("get_json('__files__')" in script or "for_each_file(" in script) and "return_json(" in script:
            return self._gsr.execute_and_parse_json(
                script,
                parameters={**parameters, '__files__': self._files},
                timeout_in_seconds=timeout_in_seconds
            )
        else:
            raise GimpMissingRequiredParameterException(
                'Either an image file must be opened with open_xcf(\'__file__\') ' +
                'and the result is returned with return_json() ' +
                'or a list of files must be retrieved by get_json(\'__files__\') or for_each_file() ' +
                'and the result is returned with return_json().'
            )

    def copy_layer_from(
            self,
            other_collection: 'GimpFileCollection',
            layer_name: str,
            layer_position: int = 0,
            other_can_be_smaller: bool = False,
            timeout_in_seconds: float = None
    ) -> 'GimpFileCollection':
        """
        Copies a layer from another collection into this collection.

        Example:

        >>> from tempfile import TemporaryDirectory
        >>> import numpy as np
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.GimpFile import GimpFile
        >>> with TemporaryDirectory('_src') as srcdir, TemporaryDirectory('_dst') as dstdir:  # doctest: +ELLIPSIS
        ...     src_1 = GimpFile(os.path.join(srcdir, 'file1.xcf')) \\
        ...         .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('White', np.ones(shape=(1, 1), dtype=np.uint8)*255)
        ...     src_2 = GimpFile(os.path.join(srcdir, 'file2.xcf')) \\
        ...         .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('White', np.ones(shape=(1, 1), dtype=np.uint8)*255)
        ...
        ...     dst_1 = GimpFile(os.path.join(dstdir, 'file1.xcf')) \\
        ...         .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('White', np.zeros(shape=(1, 1), dtype=np.uint8)*255)
        ...     dst_2 = GimpFile(os.path.join(dstdir, 'file2.xcf')) \\
        ...         .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8))
        ...
        ...     src_collection = GimpFileCollection([src_1.get_file(), src_2.get_file()])
        ...     dst_collection = GimpFileCollection([dst_1.get_file(), dst_2.get_file()])
        ...
        ...     dst_collection.copy_layer_from(src_collection, 'White', layer_position=1, timeout_in_seconds=10)
        ...
        ...     np.all(dst_1.layer_to_numpy('White') == 255) \\
        ...         and ['Background', 'White'] == dst_1.layer_names() \\
        ...         and 'White' in dst_2.layer_names() \\
        ...         and np.all(dst_2.layer_to_numpy('White') == 255) \\
        ...         and ['Background', 'White'] == dst_2.layer_names()
        <...>
        True

        :param other_collection: The collection from which to take the layer.
        :param layer_name: Name of the layer to copy.
        :param layer_position: Layer position in the destination image.
        :param other_can_be_smaller: Whether the other collection must at least contain all the
               elements of the current collection or not.
        :param timeout_in_seconds: Script execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFileCollection.GimpFileCollection`
        """
        prefix_in_other_collection = other_collection.get_prefix()
        files_in_other_collection = map(lambda file: file[len(prefix_in_other_collection):], other_collection._files)
        prefix_in_this_collection = self.get_prefix()
        files_in_this_collection = map(lambda file: file[len(prefix_in_this_collection):], other_collection._files)
        missing = set()
        if not other_can_be_smaller:
            missing = set(files_in_this_collection) - set(files_in_other_collection)
        if missing:
            raise MissingFilesException(
                'The other collection is smaller than this collection by the following entries: ' +
                ', '.join(missing)
            )

        script = textwrap.dedent(
            """
            import os
            from pgimp.gimp.parameter import get_json, get_string, get_int, get_bool, return_json
            from pgimp.gimp.layer import copy_or_merge_layer
            from pgimp.gimp.file import XcfFile

            prefix_in_other_collection = get_string('prefix_in_other_collection')
            prefix_in_this_collection = get_string('prefix_in_this_collection')
            layer_name = get_string('layer_name')
            layer_position = get_int('layer_position')
            other_can_be_smaller = get_bool('other_can_be_smaller')
            files = get_json('__files__')

            for file in files:
                file = file[len(prefix_in_this_collection):]
                file_src = os.path.join(prefix_in_other_collection, file)
                file_dst = os.path.join(prefix_in_this_collection, file)
                if other_can_be_smaller and not os.path.exists(file_src):
                    continue

                with XcfFile(file_src) as image_src, XcfFile(file_dst, save=True) as image_dst:
                    copy_or_merge_layer(image_src, layer_name, image_dst, layer_name, layer_position)

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
                'other_can_be_smaller': other_can_be_smaller,
            },
            timeout_in_seconds=timeout_in_seconds
        )
        return self

    def merge_mask_layer_from(
            self, other_collection: 'GimpFileCollection',
            layer_name: str,
            mask_foreground_color: MaskForegroundColor = MaskForegroundColor.WHITE,
            layer_position: int = 0,
            timeout_in_seconds: float = None
    ):
        """
        Merge masks together. Masks should contain grayscale values or have an rgb gray value (r, g, b)
        with r == g == b. In case of rgb, the componentwise minimum or maximum will be taken depending
        on the foreground color. When the mask foreground color is white, then the maximum of values is
        taken when merging. Otherwise the minimum is taken.

        Example:

        >>> from tempfile import TemporaryDirectory
        >>> import numpy as np
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.GimpFile import GimpFile
        >>> with TemporaryDirectory('_src') as srcdir, TemporaryDirectory('_dst') as dstdir:  # doctest: +ELLIPSIS
        ...     src_1 = GimpFile(os.path.join(srcdir, 'file1.xcf')) \\
        ...         .create('Mask', np.array([[255, 0]], dtype=np.uint8))
        ...
        ...     dst_1 = GimpFile(os.path.join(dstdir, 'file1.xcf')) \\
        ...         .create('Mask', np.array([[0, 255]], dtype=np.uint8))
        ...     dst_2 = GimpFile(os.path.join(dstdir, 'file2.xcf')) \\
        ...         .create('Mask', np.array([[0, 255]], dtype=np.uint8))
        ...
        ...     src_collection = GimpFileCollection([src_1.get_file()])
        ...     dst_collection = GimpFileCollection([dst_1.get_file(), dst_2.get_file()])
        ...
        ...     dst_collection.merge_mask_layer_from(
        ...         src_collection, 'Mask', MaskForegroundColor.WHITE, timeout_in_seconds=10)
        ...
        ...     np.all(dst_1.layer_to_numpy('Mask') == [[255], [255]]) \\
        ...         and ['Mask'] == dst_1.layer_names() \\
        ...         and 'Mask' in dst_2.layer_names() \\
        ...         and np.all(dst_2.layer_to_numpy('Mask') == [[0], [255]]) \\
        ...         and ['Mask'] == dst_2.layer_names()
        <...>
        True

        :param other_collection: The collection from which to merge the mask.
        :param layer_name: Name of the layer to copy.
        :param mask_foreground_color: when white, the maximum is taken, when black, the minimum values are taken
               when merging
        :param layer_position: Layer position in the destination image.
        :param timeout_in_seconds: Script execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFileCollection.GimpFileCollection`
        """
        prefix_in_other_collection = other_collection.get_prefix()
        prefix_in_this_collection = self.get_prefix()

        script = textwrap.dedent(
            """
            import os
            from pgimp.gimp.file import XcfFile
            from pgimp.gimp.parameter import get_json, get_string, get_int, return_json
            from pgimp.gimp.layer import merge_mask_layer

            prefix_in_other_collection = get_string('prefix_in_other_collection')
            prefix_in_this_collection = get_string('prefix_in_this_collection')
            layer_name = get_string('layer_name')
            layer_position = get_int('layer_position')
            mask_foreground_color = get_int('mask_foreground_color')
            files = get_json('__files__')

            for file in files:
                file = file[len(prefix_in_this_collection):]
                file_src = os.path.join(prefix_in_other_collection, file)
                file_dst = os.path.join(prefix_in_this_collection, file)
                if not os.path.exists(file_src):
                    continue
                with XcfFile(file_src) as image_src, XcfFile(file_dst, save=True) as image_dst:
                    merge_mask_layer(
                        image_src,
                        layer_name,
                        image_dst,
                        layer_name,
                        mask_foreground_color,
                        layer_position
                    )

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
                'mask_foreground_color': mask_foreground_color.value,
            },
            timeout_in_seconds=timeout_in_seconds
        )
        return self

    def clear_selection(
        self,
        timeout_in_seconds: float = None
    ):
        """
        Clears active selections.

        :param timeout_in_seconds: Script execution timeout in seconds.
        """
        script = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.parameter import get_json, return_json
            from pgimp.gimp.file import XcfFile
            
            files = get_json('__files__')
            for file in files:
                with XcfFile(file, save=True) as image:
                    gimp.pdb.gimp_selection_none(image)
            
            return_json(None)
            """
        )
        self.execute_script_and_return_json(
            script,
            timeout_in_seconds=timeout_in_seconds
        )

    def remove_layers_by_name(
        self,
        layer_names: List[str],
        timeout_in_seconds: float = None
    ):
        """
        Removes layers by name.

        Example:

        >>> from tempfile import TemporaryDirectory
        >>> import numpy as np
        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from pgimp.GimpFile import GimpFile
        >>> data = np.array([[0, 255]], dtype=np.uint8)
        >>> with TemporaryDirectory('_files') as dir:
        ...    file1 = GimpFile(os.path.join(dir, 'file1.xcf')) \\
        ...        .create('Background', data) \\
        ...        .add_layer_from_numpy('Layer 1', data) \\
        ...        .add_layer_from_numpy('Layer 2', data) \\
        ...        .add_layer_from_numpy('Layer 3', data)
        ...    file2 = GimpFile(os.path.join(dir, 'file2.xcf')) \\
        ...        .create('Background', data) \\
        ...        .add_layer_from_numpy('Layer 1', data) \\
        ...        .add_layer_from_numpy('Layer 2', data)
        ...
        ...    collection = GimpFileCollection([file1.get_file(), file2.get_file()])
        ...    collection.remove_layers_by_name(['Layer 1', 'Layer 3'], timeout_in_seconds=10)
        ...
        ...    [file1.layer_names(), file2.layer_names()]
        [['Layer 2', 'Background'], ['Layer 2', 'Background']]

        :param layer_names: List of layer names.
        :param timeout_in_seconds: Script execution timeout in seconds.
        """
        script = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.parameter import get_json, return_json
            from pgimp.gimp.file import XcfFile
            
            files = get_json('__files__')
            layer_names = get_json('layer_names')
            for file in files:
                with XcfFile(file, save=True) as image:
                    for layer_name in layer_names:
                        layer = gimp.pdb.gimp_image_get_layer_by_name(image, layer_name)
                        if layer is not None:
                            gimp.pdb.gimp_image_remove_layer(image, layer)
            
            return_json(None)
            """
        )
        self.execute_script_and_return_json(
            script,
            parameters={'layer_names': layer_names},
            timeout_in_seconds=timeout_in_seconds
        )

    @classmethod
    def create_from_pathname(cls, pathname: str):
        """
        Create a collection of gimp files by pathname.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from tempfile import TemporaryDirectory
        >>> import numpy as np
        >>> with TemporaryDirectory('gfc') as tmpdir:
        ...     gf1 = GimpFile(os.path.join(tmpdir, 'f1.xcf')) \\
        ...         .create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(os.path.join(tmpdir, 'f2.xcf')) \\
        ...         .create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_pathname(tmpdir)
        ...     gfc.replace_prefix(gfc.get_prefix()).get_files()
        ['f1.xcf', 'f2.xcf']

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

    @classmethod
    def create_from_gimp_files(cls, gimp_files: List[GimpFile]):
        """
        Create a collection of gimp files by a list of :py:class:`~pgimp.GimpFile.GimpFile`.

        Example:

        >>> from pgimp.GimpFileCollection import GimpFileCollection
        >>> from tempfile import TemporaryDirectory
        >>> import numpy as np
        >>> with TemporaryDirectory('gfc') as tmpdir:
        ...     gf1 = GimpFile(os.path.join(tmpdir, 'f1.xcf')) \\
        ...         .create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gf2 = GimpFile(os.path.join(tmpdir, 'f2.xcf')) \\
        ...         .create('Foreground', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gfc = GimpFileCollection.create_from_gimp_files([gf1, gf2])
        ...     gfc.replace_prefix(gfc.get_prefix()).get_files()
        ['f1.xcf', 'f2.xcf']

        :param gimp_files: The list of gimp files to be contained in the collection.
        :return: A :py:class:`~pgimp.GimpFileCollection.GimpFileCollection` that contains an ordered list of filenames.
        """

        return cls(list(map(lambda f: f.get_file(), gimp_files)))
