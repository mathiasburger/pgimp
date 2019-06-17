# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import io
import os
import tempfile
import textwrap
from enum import Enum
from typing import List, Union, Tuple, Optional

import numpy as np

import gimpenums
from pgimp.GimpException import GimpException
from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.layers.Layer import Layer
from pgimp.util import file
from pgimp.util.string import escape_single_quotes

EXTENSION = '.xcf'


class GimpFileType(Enum):
    RGB = 0
    GRAY = 1
    INDEXED = 2


class LayerType(Enum):
    INDEXED = 4


class ColorMap(Enum):
    JET = 'COLORMAP_JET'


image_type_to_layer_type = {
    GimpFileType.RGB: 0,
    GimpFileType.GRAY: 2,
}


class DataFormatException(GimpException):
    """
    Indicates that data is in an unexpected or wrong format.
    """
    pass


class GimpFile:
    """
    Encapsulates functionality related to modifying gimp's xcf files and retreiving information from them.

    When interacting with numpy, please note that the array must be row-major (y,x-indexed).

    Example:

    >>> from pgimp.GimpFile import GimpFile
    >>> from pgimp.util.TempFile import TempFile
    >>> import numpy as np
    >>> with TempFile('.xcf') as f:
    ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(32, 32), dtype=np.uint8))
    ...     gimp_file.layer_names()
    ['Background']
    """

    def __init__(
        self,
        file: str,
        short_running_timeout_in_seconds: int = 10,
        long_running_timeout_in_seconds: int = 20,
    ) -> None:
        super().__init__()
        self._file = file
        self._gsr = GimpScriptRunner()
        self.long_running_timeout_in_seconds = long_running_timeout_in_seconds
        self.short_running_timeout_in_seconds = short_running_timeout_in_seconds

    def get_file(self):
        """
        Returns the filename.

        :return: Filename.
        """
        return self._file

    def create(
        self,
        layer_name: str,
        layer_content: np.ndarray,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Create a new gimp image with one layer from a numpy array.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(32, 32), dtype=np.uint8))
        ...     gimp_file.layer_names()
        ['Background']

        :param layer_name: Name of the layer to create.
        :param layer_content: Layer content, usually in the format of unsigned 8 bit integers.
        :param timeout: Execution timeout in seconds.
        :return: The newly created :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        height, width, depth, image_type, layer_type = self._numpy_array_info(layer_content)

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.file import save_xcf
            from pgimp.gimp.layer import add_layer_from_numpy

            image = gimp.pdb.gimp_image_new({0:d}, {1:d}, {2:d})
            add_layer_from_numpy(image, '{6:s}', '{5:s}', image.width, image.height, {4:d})
            save_xcf(image, '{3:s}')
            """
        ).format(
            width,
            height,
            image_type.value,
            escape_single_quotes(self._file),
            layer_type,
            escape_single_quotes(layer_name),
            escape_single_quotes(tmpfile)
        )

        self._gsr.execute(
            code,
            timeout_in_seconds=self.long_running_timeout_in_seconds if timeout is None else timeout
        )

        os.remove(tmpfile)
        return self

    def create_empty(
        self,
        width: int,
        height: int,
        type: GimpFileType = GimpFileType.RGB,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Creates an empty image without any layers.

        Example:

        >>> from pgimp.GimpFile import GimpFile, GimpFileType
        >>> from pgimp.util.TempFile import TempFile
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create_empty(3, 2, GimpFileType.RGB)
        ...     gimp_file.layer_names()
        []

        :param width: Image width.
        :param height: Image height.
        :param type: Image type, e.g. rgb or gray.
        :param timeout: Execution timeout in seconds.
        :return: The newly created :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        code = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.file import save_xcf
            image = gimp.pdb.gimp_image_new({0:d}, {1:d}, {2:d})
            save_xcf(image, '{3:s}')
            """
        ).format(width, height, type.value, escape_single_quotes(self._file))

        self._gsr.execute(
            code,
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        return self

    def create_indexed(
        self,
        layer_name: str,
        layer_content: np.ndarray,
        colormap: Union[np.ndarray, ColorMap],
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Create a new indexed gimp image with one layer from a numpy array. An indexed image has a single channel
        and displays the values using a colormap.

        Example using a predefined colormap:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.GimpFile import ColorMap
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create_indexed(
        ...         'Background',
        ...         np.arange(0, 256, dtype=np.uint8).reshape((1, 256)),
        ...         ColorMap.JET
        ...     )

        Example using a custom colormap:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> from pgimp.GimpFile import ColorMap
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create_indexed(
        ...         'Background',
        ...         np.arange(0, 256, dtype=np.uint8).reshape((1, 256)),
        ...         np.array(
        ...             [[255, 0, 0], [0, 255, 0], [0, 0, 255], *[[i, i, i] for i in range(3, 256)]],
        ...             dtype=np.uint8
        ...         )
        ...     )

        :param layer_name: Name of the layer to create.
        :param layer_content: Layer content, usually in the format of unsigned 8 bit integers.
        :param timeout: Execution timeout in seconds.
        :return: The newly created :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        if isinstance(colormap, np.ndarray):
            if not len(layer_content.shape) == 2 and not (len(layer_content.shape) == 3 and layer_content.shape[2] == 1):
                raise DataFormatException('Indexed images can only contain one channel')
            colormap = 'np.frombuffer({0}, dtype=np.uint8).reshape((256, 3))'.format(colormap.tobytes())
        if isinstance(colormap, ColorMap):
            colormap = colormap.value

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            from pgimp.gimp.file import save_xcf
            from pgimp.gimp.colormap import *  # necessary for predefined colormaps
            from pgimp.gimp.layer import add_layer_from_numpy

            cmap = {0:s}
            image = gimp.pdb.gimp_image_new({1:d}, {2:d}, gimpenums.GRAY)
            palette_name = gimp.pdb.gimp_palette_new('colormap')
            for i in range(0, cmap.shape[0]):
                gimp.pdb.gimp_palette_add_entry(palette_name, str(i), (int(cmap[i][0]), int(cmap[i][1]), int(cmap[i][2])))
            gimp.pdb.gimp_convert_indexed(image, gimpenums.NO_DITHER, gimpenums.CUSTOM_PALETTE, 256, False, False, palette_name)

            add_layer_from_numpy(image, '{5:s}', '{4:s}', image.width, image.height, gimpenums.INDEXED_IMAGE)
            save_xcf(image, '{3:s}')
            """
        ).format(
            colormap,
            layer_content.shape[1],
            layer_content.shape[0],
            escape_single_quotes(self._file),
            escape_single_quotes(layer_name),
            escape_single_quotes(tmpfile)
        )

        self._gsr.execute(
            code,
            timeout_in_seconds=self.long_running_timeout_in_seconds if timeout is None else timeout
        )

        os.remove(tmpfile)
        return self

    def create_from_template(
        self,
        other_file: 'GimpFile',
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Create a new gimp file without any layers from a template containing the dimensions (width, height)
        and the image type.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> with TempFile('.xcf') as original, TempFile('.xcf') as created:
        ...     original_file = GimpFile(original).create('Background', np.zeros(shape=(3, 2), dtype=np.uint8))
        ...     created_file = GimpFile(created).create_from_template(original_file)
        ...     created_file.layer_names()
        []

        :param other_file: The template file.
        :param timeout: Execution timeout in seconds.
        :return: The newly created :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import save_xcf
            from pgimp.gimp.image import create_from_template_file
            image = create_from_template_file('{0:s}')
            save_xcf(image, '{1:s}')
            """
        ).format(escape_single_quotes(other_file._file), escape_single_quotes(self._file))

        self._gsr.execute(
            code,
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        return self

    def create_from_file(
        self,
        file: str,
        layer_name: str = 'Background',
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Create a new gimp file by importing an image from another format.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as xcf, TempFile('.png') as png, TempFile('.xcf') as from_png:
        ...     gimp_file = GimpFile(xcf) \\
        ...         .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('Foreground', np.ones(shape=(1, 1), dtype=np.uint8)*255, opacity=50.) \\
        ...         .export(png)  # saved as grayscale with alpha (identify -format '%[channels]' FILE)
        ...     GimpFile(from_png).create_from_file(png, layer_name='Image').layer_to_numpy('Image')
        array([[[127, 255]]], dtype=uint8)

        :param file: File to import into gimp.
        :param layer_name: The layer name for the data to be imported.
        :param timeout: Execution timeout in seconds.
        :return:
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import save_xcf
            from pgimp.gimp.image import create_from_file
            image = create_from_file('{0:s}')
            image.layers[0].name = '{2:s}'
            save_xcf(image, '{1:s}')
            """
        ).format(
            escape_single_quotes(file),
            escape_single_quotes(self._file),
            escape_single_quotes(layer_name)
        )

        self._gsr.execute(
            code,
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        return self

    def copy(
        self,
        filename: str,
    ) -> 'GimpFile':
        """
        Copies a gimp file.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> with TempFile('.xcf') as original, TempFile('.xcf') as copy:
        ...     original_file = GimpFile(original).create('Background', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     copied_file = original_file.copy(copy)
        ...     copied_file.layer_names()
        ['Background']

        :param filename: Destination filename relative to the source filename. Or an absolute path.
        :return: The copied exemplar of :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        dst = file.copy_relative(self._file, filename)
        return GimpFile(dst)

    def layer_to_numpy(
        self,
        layer_name: str,
        timeout: Optional[int] = None,
    ) -> np.ndarray:
        """
        Convert a gimp layer to a numpy array of unsigned 8 bit integers.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(1, 2, 1), dtype=np.uint8))
        ...     gimp_file.layer_to_numpy('Background').shape
        (1, 2, 1)

        :param layer_name: Name of the layer to convert.
        :param timeout: Execution timeout in seconds.
        :return: Numpy array of unsigned 8 bit integers.
        """
        return self.layers_to_numpy(
            [layer_name],
            timeout=self.long_running_timeout_in_seconds if timeout is None else timeout
        )

    def layers_to_numpy(
        self,
        layer_names: List[str],
        timeout: Optional[int] = None,
    ) -> np.ndarray:
        """
        Convert gimp layers to a numpy array of unsigned 8 bit integers.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f) \\
        ...         .create('Red', np.zeros(shape=(1, 2, 1), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('Green', np.ones(shape=(1, 2, 1), dtype=np.uint8)*127) \\
        ...         .add_layer_from_numpy('Blue', np.ones(shape=(1, 2, 1), dtype=np.uint8)*255)
        ...     gimp_file.layers_to_numpy(['Red', 'Green', 'Blue']).shape
        (1, 2, 3)

        :param layer_names: Names of the layers to convert.
        :param timeout: Execution timeout in seconds.
        :return: Numpy array of unsigned 8 bit integers.
        """
        bytes = self._gsr.execute_binary(
            textwrap.dedent(
                """
                import numpy as np
                import sys
                from pgimp.gimp.file import open_xcf
                from pgimp.gimp.parameter import get_json
                from pgimp.gimp.layer import convert_layers_to_numpy

                np_buffer = convert_layers_to_numpy(open_xcf('{0:s}'), get_json('layer_names', '[]'))
                np.save(sys.stdout, np_buffer)
                """,
            ).format(escape_single_quotes(self._file)),
            parameters={'layer_names': layer_names},
            timeout_in_seconds=self.long_running_timeout_in_seconds if timeout is None else timeout
        )

        return np.load(io.BytesIO(bytes))

    def add_layer_from_numpy(
        self,
        layer_name: str,
        layer_content: np.ndarray,
        opacity: float = 100.0,
        visible: bool = True,
        position: Union[int, str] = 0,
        type: LayerType = None,
        blend_mode: Union[int, List[int]] = gimpenums.NORMAL_MODE,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Adds a new layer to the gimp file from numpy data, usually as unsigned 8 bit integers.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:  # doctest:+ELLIPSIS
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(1, 2), dtype=np.uint8))
        ...     gimp_file.add_layer_from_numpy('Foreground', np.ones(shape=(1, 2), dtype=np.uint8)*255, opacity=55., visible=False)
        ...     gimp_file.layer_names()
        <...>
        ['Foreground', 'Background']

        :param layer_name: Name of the layer to add.
        :param layer_content: Layer content, usually as unsigned 8 bit integers.
        :param opacity: How transparent the layer should be (opacity is the inverse of transparency).
        :param visible: Whether the layer should be visible.
        :param position: Position in the stack of layers. On top = 0, bottom = number of layers.
            In case a layer name is specified, the new layer will be added on top of the layer with the given name.
        :param type: Layer type. Indexed images should use indexed layers.
        :param blend_mode: Affects the display of the current layer. Blend mode normal means no blending.
        :param timeout: Execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        return self.add_layers_from_numpy(
            [layer_name],
            np.expand_dims(layer_content, axis=0),
            opacity,
            visible,
            position,
            type,
            blend_mode,
            timeout
        )

    def add_layers_from_numpy(
        self,
        layer_names: List[str],
        layer_contents: np.ndarray,
        opacity: Union[float, List[float]] = 100.0,
        visible: Union[bool, List[bool]] = True,
        position: Union[int, str] = 0,
        type: LayerType = None,
        blend_mode: Union[int, List[int]] = gimpenums.NORMAL_MODE,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Adds new layers to the gimp file from numpy data, usually as unsigned 8 bit integers.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:  # doctest:+ELLIPSIS
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(1, 2), dtype=np.uint8))
        ...     gimp_file.add_layers_from_numpy(['Layer 1', 'Layer 2'], np.ones(shape=(2, 1, 2), dtype=np.uint8)*255, opacity=55., visible=False, position='Background')
        ...     gimp_file.layer_names()
        <...>
        ['Layer 1', 'Layer 2', 'Background']

        :param layer_names: Names of the layers to add.
        :param layer_contents: Layer content, usually as unsigned 8 bit integers. First axis indexes the layer.
        :param opacity: How transparent the layer should be (opacity is the inverse of transparency).
        :param visible: Whether the layer should be visible.
        :param position: Position in the stack of layers. On top = 0, bottom = number of layers.
            In case a layer name is specified, the new layers will be added on top of the layer with the given name.
        :param type: Layer type. Indexed images should use indexed layers.
        :param blend_mode: Affects the display of the current layer. Blend mode normal means no blending.
        :param timeout: Execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        if len(layer_contents) == 0:
            raise ValueError('Layer contents must not be empty')
        if len(layer_contents) != len(layer_names):
            raise ValueError('Layer contents must exist for each layer name.')

        height, width, depth, image_type, layer_type = self._numpy_array_info(layer_contents[0])
        if type is not None:
            layer_type = type.value

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_contents)

        code = textwrap.dedent(
            """
            from pgimp.gimp.file import XcfFile
            from pgimp.gimp.layer import add_layers_from_numpy
            from pgimp.gimp.parameter import get_json, get_int, get_string
            
            with XcfFile(get_string('file'), save=True) as image:
                position = get_json('position')[0]
                add_layers_from_numpy(
                    image, get_string('tmpfile'), 
                    get_json('layer_names'), 
                    get_int('width'), 
                    get_int('height'), 
                    get_int('layer_type'), 
                    position, 
                    get_json('opacity')[0],
                    get_json('blend_mode')[0], 
                    get_json('visible')[0]
                )
            """
        )

        self._gsr.execute(
            code,
            parameters={
                'width': width,
                'height': height,
                'file': self._file,
                'layer_type': layer_type,
                'layer_names': layer_names,
                'tmpfile': tmpfile,
                'visible': [visible],
                'opacity': [opacity],
                'position': [position],
                'blend_mode': [blend_mode],
            },
            timeout_in_seconds=self.long_running_timeout_in_seconds if timeout is None else timeout
        )

        os.remove(tmpfile)
        return self

    def _numpy_array_info(self, content: np.ndarray):
        if content.dtype != np.uint8:
            raise DataFormatException('Only uint8 is supported')

        if len(content.shape) == 2:
            height, width = content.shape
            depth = 1
        elif len(content.shape) == 3 and content.shape[2] in [1, 3]:
            height, width, depth = content.shape
        else:
            raise DataFormatException('Unrecognized input data shape: ' + repr(content.shape))

        if depth == 1:
            image_type = GimpFileType.GRAY
        elif depth == 3:
            image_type = GimpFileType.RGB
        else:
            raise DataFormatException('Wrong image depth {:d}'.format(depth))

        layer_type = image_type_to_layer_type[image_type]

        return height, width, depth, image_type, layer_type

    def add_layer_from_file(
        self,
        other_file: 'GimpFile',
        name: str,
        new_name: str = None,
        new_type: GimpFileType = GimpFileType.RGB,
        new_position: int = 0,
        new_visibility: Optional[bool] = None,
        new_opacity: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Adds a new layer to the gimp file from another gimp file.

        Example:

        >>> from pgimp.GimpFile import GimpFile, GimpFileType
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as other, TempFile('.xcf') as current:  # doctest:+ELLIPSIS
        ...     green_content = np.zeros(shape=(1, 1, 3), dtype=np.uint8)
        ...     green_content[:, :] = [0, 255, 0]
        ...     other_file = GimpFile(other).create('Green', green_content)
        ...     current_file = GimpFile(current).create('Background', np.zeros(shape=(1, 1, 3), dtype=np.uint8))
        ...     current_file.add_layer_from_file(
        ...         other_file,
        ...         'Green',
        ...         new_name='Green (copied)',
        ...         new_type=GimpFileType.RGB, new_position=1
        ...     )
        ...     current_file.layer_names()
        ...     current_file.layer_to_numpy('Green (copied)')
        <...>
        ['Background', 'Green (copied)']
        array([[[  0, 255,   0]]], dtype=uint8)

        :param other_file: The gimp file from which to copy the layer into the current image.
        :param name: The layer name in the other file to copy over to the current file. Also the layer name
                     in the current file if no new name is set.
        :param new_name: The new layer name in the current image. Same as the layer name in the other file if not set.
        :param new_type: The layer type to create in the current image. E.g. rgb or grayscale.
        :param new_position: Position in the stack of layers. On top = 0, bottom = number of layers.
        :param new_visibility: Visibility of the layer if it should be changed.
        :param new_opacity: Opacity for the layer if it should be changed.
        :param timeout: Execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.parameter import get_json
            from pgimp.gimp.file import XcfFile
            from pgimp.gimp.layer import copy_layer
            
            params = get_json('params')
            new_position = params['new_position']
            new_visibility = params['new_visibility']
            new_opacity = params['new_opacity']

            with XcfFile('{1:s}') as image_src, XcfFile('{0:s}', save=True) as image_dst:
                copy_layer(image_src, '{3:s}', image_dst, '{2:s}', new_position)
                if new_visibility is not None:
                    image_dst.layers[new_position].visible = new_visibility
                if new_opacity is not None:
                    image_dst.layers[new_position].opacity = float(new_opacity)
            """
        ).format(
            escape_single_quotes(self._file),
            escape_single_quotes(other_file._file),
            escape_single_quotes(new_name or name),
            escape_single_quotes(name),
            new_type.value,
        )

        self._gsr.execute(
            code, 
            timeout_in_seconds=self.long_running_timeout_in_seconds if timeout is None else timeout,
            parameters={
                'params': {
                    'new_visibility': new_visibility,
                    'new_position': new_position,
                    'new_opacity': new_opacity,
                }
            }
        )
        return self

    def merge_layer_from_file(
        self,
        other_file: 'GimpFile',
        name: str,
        clear_selection: bool = True,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Merges a layer from another file into the current file. The layer must exist in the current file.

        Example:

        >>> from pgimp.GimpFile import GimpFile, GimpFileType
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as other, TempFile('.xcf') as current:  # doctest:+ELLIPSIS
        ...     green_content = np.zeros(shape=(1, 1, 3), dtype=np.uint8)
        ...     green_content[:, :] = [0, 255, 0]
        ...     other_file = GimpFile(other).create('Green', green_content)
        ...     current_file = GimpFile(current).create('Green', np.zeros(shape=(1, 1, 3), dtype=np.uint8))
        ...     current_file.merge_layer_from_file(other_file, 'Green')
        ...     current_file.layer_names()
        ...     current_file.layer_to_numpy('Green')
        <...>
        ['Green']
        array([[[  0, 255,   0]]], dtype=uint8)

        :param other_file: The gimp file from which the layer contents are merged into the current file.
        :param name: Name of the layer to merge.
        :param clear_selection: Clear selection before merging to avoid only merging the selection.
        :param timeout: Execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import XcfFile
            from pgimp.gimp.layer import merge_layer

            with XcfFile('{1:s}') as image_src, XcfFile('{0:s}', save=True) as image_dst:
                merge_layer(image_src, '{2:s}', image_dst, '{2:s}', 0, {3:s})
            """
        ).format(
            escape_single_quotes(self._file),
            escape_single_quotes(other_file._file),
            escape_single_quotes(name),
            str(clear_selection)
        )

        self._gsr.execute(
            code, 
            timeout_in_seconds=self.long_running_timeout_in_seconds if timeout is None else timeout
        )
        return self

    def layers(
        self,
        timeout: Optional[int] = None,
    ) -> List[Layer]:
        """
        Returns the image layers. The topmost layer is the first element, the bottommost the last element.
        
        :param timeout: Execution timeout in seconds.
        :return: List of :py:class:`~pgimp.layers.Layer`.
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import open_xcf
            from pgimp.gimp.parameter import return_json

            image = open_xcf('{0:s}')

            result = []
            for layer in image.layers:
                properties = dict()
                properties['name'] = layer.name
                properties['visible'] = layer.visible
                properties['opacity'] = layer.opacity
                result.append(properties)

            return_json(result)
            """.format(escape_single_quotes(self._file))
        )

        result = self._gsr.execute_and_parse_json(
            code, 
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        layers = []
        for idx, layer_properties in enumerate(result):
            layer_properties['position'] = idx
            layers.append(Layer(layer_properties))

        return layers

    def layer_names(
        self,
        timeout: Optional[int] = None,
    ) -> List[str]:
        """
        Returns the names of the layers in the gimp file. The topmost layer is the first element,
        the bottommost the last element.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as file:
        ...     gimp_file = GimpFile(file) \\
        ...         .create('Background', np.zeros(shape=(2, 2), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('Black', np.zeros(shape=(2, 2), dtype=np.uint8))
        ...     gimp_file.layer_names()
        ['Black', 'Background']
        
        :param timeout: Execution timeout in seconds.
        :return: List of layer names.
        """
        return list(map(lambda l: l.name, self.layers(
            timeout=self.short_running_timeout_in_seconds if timeout is None else timeout)))

    def remove_layer(
        self,
        layer_name: str,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Removes a layer from the gimp file.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as file:
        ...     gimp_file = GimpFile(file) \\
        ...         .create('Background', np.zeros(shape=(2, 2), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('Black', np.zeros(shape=(2, 2), dtype=np.uint8)) \\
        ...         .remove_layer('Background')
        ...     gimp_file.layer_names()
        ['Black']

        :param layer_name: Name of the layer to remove.
        :param timeout: Execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import XcfFile
            from pgimp.gimp.layer import remove_layer

            with XcfFile('{0:s}', save=True) as image:
                remove_layer(image, '{1:s}')
            """
        ).format(escape_single_quotes(self._file), escape_single_quotes(layer_name))

        self._gsr.execute(
            code, 
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        return self

    def dimensions(
        self,
        timeout: Optional[int] = None,
    ) -> Tuple[int, int]:
        """
        Return the image dimensions (width, height).

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(3, 2), dtype=np.uint8))
        ...     gimp_file.dimensions()
        (2, 3)

        :param timeout: Execution timeout in seconds.
        :return: Tuple of width and height.
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import open_xcf
            from pgimp.gimp.parameter import return_json

            image = open_xcf('{0:s}')
            return_json([image.width, image.height])
            """
        ).format(escape_single_quotes(self._file))

        dimensions = self._gsr.execute_and_parse_json(
            code, 
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        return tuple(dimensions)

    def export(
        self,
        file: str,
        timeout: Optional[int] = None,
    ) -> 'GimpFile':
        """
        Export a gimp file to another file format based on the file extension.

        Gimp will apply defaults for encoding to the desired format. E.g. png is saved including an alpha channel
        and jpg has no alpha channel but will use default compression settings.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as xcf, TempFile('.png') as png, TempFile('.xcf') as from_png:
        ...     gimp_file = GimpFile(xcf) \\
        ...         .create('Background', np.zeros(shape=(1, 1), dtype=np.uint8)) \\
        ...         .add_layer_from_numpy('Foreground', np.ones(shape=(1, 1), dtype=np.uint8)*255, opacity=50.) \\
        ...         .export(png)  # saved as grayscale with alpha (identify -format '%[channels]' FILE)
        ...     GimpFile(from_png).create_from_file(png, layer_name='Image').layer_to_numpy('Image')
        array([[[127, 255]]], dtype=uint8)

        :param file: Filename including the desired extension to export to.
        :param timeout: Execution timeout in seconds.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """

        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            from pgimp.gimp.file import XcfFile
            with XcfFile('{0:s}') as image:
                merged = gimp.pdb.gimp_image_merge_visible_layers(image, gimpenums.CLIP_TO_IMAGE)
                gimp.pdb.gimp_file_save(image, merged, '{1:s}', '{1:s}')
            """
        ).format(escape_single_quotes(self._file), escape_single_quotes(file))

        self._gsr.execute(
            code, 
            timeout_in_seconds=self.short_running_timeout_in_seconds if timeout is None else timeout
        )
        return self
