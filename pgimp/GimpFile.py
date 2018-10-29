import io
import tempfile
import textwrap
from enum import Enum

import numpy as np

from pgimp.GimpException import GimpException
from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.util import file


class GimpFileType(Enum):
    RGB = 0
    GRAY = 1


image_type_to_layer_type = {
    GimpFileType.RGB: 0,
    GimpFileType.GRAY: 2,
}


class DataFormatException(GimpException):
    pass


class GimpFile:
    def __init__(self, file: str) -> None:
        super().__init__()
        self._file = file
        self._gsr = GimpScriptRunner()

    def create(self, layer_name: str, layer_content: np.ndarray):
        if len(layer_content.shape) == 2:
            height, width = layer_content.shape
            depth = 1
        elif len(layer_content.shape) == 3 and layer_content.shape[2] in [1, 3]:
            height, width, depth = layer_content.shape
        else:
            raise DataFormatException('Unrecognized input data shape: ' + repr(layer_content.shape))

        if depth == 1:
            type = GimpFileType.GRAY
        elif depth == 3:
            type = GimpFileType.RGB
        else:
            raise DataFormatException('Wrong image depth {:d}'.format(depth))

        tmpfile = tempfile.mktemp(suffix='.npy')
        np.save(tmpfile, layer_content)

        self._gsr.execute(textwrap.dedent(
            """
            import gimp
            import gimpenums
            import numpy as np
            
            image = gimp.pdb.gimp_image_new({0:d}, {1:d}, {2:d})
            layer = gimp.pdb.gimp_layer_new(image, image.width, image.height, {4:d}, '{5:s}', 100, gimpenums.NORMAL_MODE)
            array = np.load('{6:s}')
            bytes = np.uint8(array).tobytes()
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes
            
            gimp.pdb.gimp_image_add_layer(image, layer, 0)
            gimp.pdb.gimp_file_save(image, layer, '{3:s}', '{3:s}')
            """
        ).format(width, height, type.value, self._file, image_type_to_layer_type[type], layer_name, tmpfile), timeout_in_seconds=2)

    def layer_to_numpy(self, layer_name: str) -> np.ndarray:
        bytes = self._gsr.execute_binary(textwrap.dedent(
            """
            import gimp
            import numpy as np
            import sys
            
            image = gimp.pdb.gimp_file_load('{0:s}', '{0:s}')
            layer_name = '{1:s}'
            layer = gimp.pdb.gimp_image_get_layer_by_name(image, layer_name)
            region = layer.get_pixel_rgn(0, 0, layer.width,layer.height)
            buffer = region[:, :]
            bpp = region.bpp
            np_buffer = np.frombuffer(buffer, dtype=np.uint8).reshape((layer.height, layer.width, bpp))
                        
            np.save(sys.stdout, np_buffer)
            """
        ).format(self._file, layer_name), timeout_in_seconds=3)

        layer = np.load(io.BytesIO(bytes))
        assert np.all(layer[0, 1] == 0)
        assert np.all(layer[1, 0] == 255)
        return layer

    def numpy_to_layer(self):
        # numpy to layer
        out2 = self._gsr.execute(textwrap.dedent(
            """
            import numpy as np

            name = '{1:s}'

            array = np.load('/tmp/test.npz')['Background']
            bytes = np.uint8(array).tobytes()
            image = gimp.Image(3, 2, RGB)
            layer = gimp.Layer(image, name, image.width, image.height, RGB_IMAGE, 100, NORMAL_MODE)
            region = layer.get_pixel_rgn(0, 0, layer.width, layer.height, True)
            region[: ,:] = bytes
            image.add_layer(layer, 0)

            gimp.pdb.gimp_file_save(image, layer, '/tmp/test.xcf', '/tmp/test.xcf')
            """
        ).format(self._file, layer), timeout_in_seconds=3)
        assert out2 != None


if __name__ == '__main__':
    gf = GimpFile(file.relative_to(__file__, 'test-resources/rgb.xcf'))
    gf.layer_to_numpy('Background')
