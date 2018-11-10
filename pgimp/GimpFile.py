import io
import os
import tempfile
import textwrap
from enum import Enum
from typing import List, Union, Tuple

import numpy as np

from pgimp.GimpException import GimpException
from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.layers.Layer import Layer
from pgimp.util import file
from pgimp.util.string import escape_single_quotes


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
    def __init__(self, file: str) -> None:
        super().__init__()
        self._file = file
        self._gsr = GimpScriptRunner()
        self._layer_conversion_timeout_in_seconds = 20
        self._short_running_timeout_in_seconds = 10

    def create(self, layer_name: str, layer_content: np.ndarray) -> 'GimpFile':
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
        :return: The newly created :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        height, width, depth, image_type, layer_type = self._numpy_array_info(layer_content)

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            import numpy as np
            from pgimp.gimp.file import save_xcf
            
            image = gimp.pdb.gimp_image_new({0:d}, {1:d}, {2:d})
            layer = gimp.pdb.gimp_layer_new(image, image.width, image.height, {4:d}, '{5:s}', 100, gimpenums.NORMAL_MODE)
            array = np.load('{6:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes
            
            gimp.pdb.gimp_image_add_layer(image, layer, 0)
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

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        os.remove(tmpfile)
        return self

    def create_empty(self, width: int, height: int, type: GimpFileType) -> 'GimpFile':
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

        self._gsr.execute(code, timeout_in_seconds=self._short_running_timeout_in_seconds)
        return self

    def create_indexed(self, layer_name: str, layer_content: np.ndarray, colormap: Union[np.ndarray, ColorMap]) -> 'GimpFile':
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
            import numpy as np
            import gimpenums
            from pgimp.gimp.file import open_xcf, save_xcf
            from pgimp.gimp.colormap import *
        
            cmap = {0:s}
            image = gimp.pdb.gimp_image_new({1:d}, {2:d}, gimpenums.GRAY)
            palette_name = gimp.pdb.gimp_palette_new('colormap')
            for i in range(0, cmap.shape[0]):
                gimp.pdb.gimp_palette_add_entry(palette_name, str(i), (int(cmap[i][0]), int(cmap[i][1]), int(cmap[i][2])))
            gimp.pdb.gimp_convert_indexed(image, gimpenums.NO_DITHER, gimpenums.CUSTOM_PALETTE, 256, False, False, palette_name)
            
            layer = gimp.pdb.gimp_layer_new(image, image.width, image.height, gimpenums.INDEXED_IMAGE, '{4:s}', 100, gimpenums.NORMAL_MODE)
            array = np.load('{5:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes
            gimp.pdb.gimp_image_add_layer(image, layer, 0)
        
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

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        os.remove(tmpfile)
        return self

    def create_from_template(self, other_file: 'GimpFile') -> 'GimpFile':
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
        :return: The newly created :py:class:`~pgimp.GimpFile.GimpFile`.
        """
        code = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.file import open_xcf, save_xcf
            image = open_xcf('{0:s}')
            width = image.width
            height = image.height
            type = image.base_type
            image = gimp.pdb.gimp_image_new(width, height, type)
            save_xcf(image, '{1:s}')
            """
        ).format(escape_single_quotes(other_file._file), escape_single_quotes(self._file))

        self._gsr.execute(code, timeout_in_seconds=self._short_running_timeout_in_seconds)
        return self

    def copy(self, filename: str) -> 'GimpFile':
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

    def layer_to_numpy(self, layer_name: str) -> np.ndarray:
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
        :return: Numpy array of unsigned 8 bit integers.
        """
        bytes = self._gsr.execute_binary(textwrap.dedent(
            """
            import gimp
            import numpy as np
            import sys
            from pgimp.gimp.file import open_xcf

            image = open_xcf('{0:s}')
            layer_name = '{1:s}'
            layer = gimp.pdb.gimp_image_get_layer_by_name(image, layer_name)
            region = layer.get_pixel_rgn(0, 0, layer.width,layer.height)
            buffer = region[:, :]
            bpp = region.bpp
            np_buffer = np.frombuffer(buffer, dtype=np.uint8).reshape((layer.height, layer.width, bpp))

            np.save(sys.stdout, np_buffer)
            """
        ).format(
            escape_single_quotes(self._file),
            escape_single_quotes(layer_name)
        ), timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        return np.load(io.BytesIO(bytes))

    def add_layer_from_numpy(self, layer_name: str, layer_content: np.ndarray, opacity: float=100.0, visible: bool=True, position: int=0, type: LayerType=None) -> 'GimpFile':
        """
        Adds a new layer to the gimp file from numpy data, usually as unsigned 8 bit integers.

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> import numpy as np
        >>> with TempFile('.xcf') as f:  # doctest:+ELLIPSIS
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(1, 2), dtype=np.uint8))
        ...     gimp_file.add_layer_from_numpy('Foreground', np.ones(shape=(1, 2)), opacity=55., visible=False)
        ...     gimp_file.layer_names()
        <...>
        ['Foreground', 'Background']

        :param layer_name: Name of the layer to add.
        :param layer_content: Layer content, usually as unsigned 8 bit integers.
        :param opacity: How transparent the layer should be (opacity is the inverse of transparency).
        :param visible: Whether the layer should be visible.
        :param position: Position in the stack of layers. On top = 0, bottom = number of layers.
        :param type: Layer type. Indexed images should use indexed layers.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        height, width, depth, image_type, layer_type = self._numpy_array_info(layer_content)
        if type is not None:
            layer_type = type.value

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            import numpy as np
            from pgimp.gimp.file import open_xcf, save_xcf

            image = open_xcf('{2:s}')
            layer = gimp.pdb.gimp_layer_new(image, {0:d}, {1:d}, {3:d}, '{4:s}', 100, gimpenums.NORMAL_MODE)
            layer.visible = {6:s}
            layer.opacity = float({7:s})
            array = np.load('{5:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes

            gimp.pdb.gimp_image_add_layer(image, layer, {8:d})
            save_xcf(image, '{2:s}')
            """
        ).format(
            width,
            height,
            escape_single_quotes(self._file),
            layer_type,
            escape_single_quotes(layer_name),
            escape_single_quotes(tmpfile),
            str(visible),
            str(opacity),
            position
        )

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)

        os.remove(tmpfile)
        return self

    def _numpy_array_info(self, content: np.ndarray):
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

    def add_layer_from_file(self, other_file: 'GimpFile', name: str, new_name: str=None, new_type: GimpFileType=GimpFileType.RGB, new_position: int=0) -> 'GimpFile':
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
        ...     current_file = GimpFile(current).create('Background', np.zeros(shape=(1, 1, 3)))
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
        :param name: The layer name in the other file to copy over to the current file. Also the layer name in the current file if no new name is set.
        :param new_name: The new layer name in the current image. Same as the layer name in the other file if not set.
        :param new_type: The layer type to create in the current image. E.g. rgb or grayscale.
        :param new_position: Position in the stack of layers. On top = 0, bottom = number of layers.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            from pgimp.gimp.file import open_xcf, save_xcf
            
            image_dst = open_xcf('{0:s}')
            image_src = open_xcf('{1:s}')
            layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, '{3:s}')
            layer_dst = gimp.pdb.gimp_layer_new(image_dst, layer_src.width, layer_src.height, {4:d}, '{2:s}', 100, gimpenums.NORMAL_MODE)
            gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, {5:d})
            gimp.pdb.gimp_edit_copy(layer_src)
            layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
            gimp.pdb.gimp_floating_sel_anchor(layer_floating)
            save_xcf(image_dst, '{0:s}')
            """
        ).format(
            escape_single_quotes(self._file),
            escape_single_quotes(other_file._file),
            escape_single_quotes(new_name or name),
            escape_single_quotes(name),
            new_type.value,
            new_position
        )

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)
        return self

    def merge_layer_from_file(self, other_file: 'GimpFile', name: str) -> 'GimpFile':
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
        ...     current_file = GimpFile(current).create('Green', np.zeros(shape=(1, 1, 3)))
        ...     current_file.merge_layer_from_file(other_file, 'Green')
        ...     current_file.layer_names()
        ...     current_file.layer_to_numpy('Green')
        <...>
        ['Green']
        array([[[  0, 255,   0]]], dtype=uint8)

        :param other_file: The gimp file from which the layer contents are merged into the current file.
        :param name: Name of the layer to merge.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        code = textwrap.dedent(
            """
            import gimp
            import gimpenums
            from pgimp.gimp.file import open_xcf, save_xcf

            image_dst = open_xcf('{0:s}')
            image_src = open_xcf('{1:s}')
            layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, '{2:s}')
            layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, '{2:s}')
            gimp.pdb.gimp_edit_copy(layer_src)
            layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
            gimp.pdb.gimp_floating_sel_anchor(layer_floating)
            save_xcf(image_dst, '{0:s}')
            """
        ).format(
            escape_single_quotes(self._file),
            escape_single_quotes(other_file._file),
            escape_single_quotes(name)
        )

        self._gsr.execute(code, timeout_in_seconds=self._layer_conversion_timeout_in_seconds)
        return self

    def layers(self) -> List[Layer]:
        """
        Returns the image layers. The topmost layer is the first element, the bottommost the last element.
        :return: List of :py:class:`~pgimp.layers.Layer`.
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import open_xcf, save_xcf
            
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

        result = self._gsr.execute_and_parse_json(code, timeout_in_seconds=self._short_running_timeout_in_seconds)
        layers = []
        for idx, layer_properties in enumerate(result):
            layer_properties['position'] = idx
            layers.append(Layer(layer_properties))

        return layers

    def layer_names(self) -> List[str]:
        """
        Returns the names of the layers in the gimp file.
        :return: List of layer names.
        """
        return list(map(lambda l: l.name, self.layers()))

    def remove_layer(self, layer_name: str) -> 'GimpFile':
        """
        Removes a layer from the gimp file.

        :param layer_name: Name of the layer to remove.
        :return: :py:class:`~pgimp.GimpFile.GimpFile`
        """
        code = textwrap.dedent(
            """
            import gimp
            from pgimp.gimp.file import open_xcf, save_xcf

            image = open_xcf('{0:s}')
            layer = gimp.pdb.gimp_image_get_layer_by_name(image, '{1:s}')
            gimp.pdb.gimp_image_remove_layer(image, layer)
            save_xcf(image, '{0:s}')
            """
        ).format(escape_single_quotes(self._file), escape_single_quotes(layer_name))

        self._gsr.execute(code, timeout_in_seconds=self._short_running_timeout_in_seconds)
        return self

    def dimensions(self) -> Tuple[int, int]:
        """
        Return the image dimensions (width, height).

        Example:

        >>> from pgimp.GimpFile import GimpFile
        >>> from pgimp.util.TempFile import TempFile
        >>> with TempFile('.xcf') as f:
        ...     gimp_file = GimpFile(f).create('Background', np.zeros(shape=(3, 2), dtype=np.uint8))
        ...     gimp_file.dimensions()
        (2, 3)

        :return: Tuple of width and height.
        """
        code = textwrap.dedent(
            """
            from pgimp.gimp.file import open_xcf
            image = open_xcf('{0:s}')
            return_json([image.width, image.height])
            """
        ).format(escape_single_quotes(self._file))

        dimensions = self._gsr.execute_and_parse_json(code, timeout_in_seconds=self._short_running_timeout_in_seconds)
        return tuple(dimensions)
