import textwrap
import numpy as np

from pgimp.GimpScriptRunner import GimpScriptRunner
from pgimp.util import file


class GimpFile:
    def __init__(self, file: str) -> None:
        super().__init__()
        self._file = file
        self._gsr = GimpScriptRunner()

    # rgb.xcf contains 3x2 image with white bg, and red, green, blue layers with differing opacity on top
    # layer 'Background' contains a black pixel at y=0, x=1, the others are white

    def layer_to_numpy(self, layer: str):
        out = self._gsr.execute(textwrap.dedent(
            """
            import numpy as np
            
            name = '{1:s}'
            image = gimp.pdb.gimp_file_load('{0:s}', '{0:s}')
            layer = gimp.pdb.gimp_image_get_layer_by_name(image, name)
            region = layer.get_pixel_rgn(0, 0, layer.width,layer.height)
            buffer = region[:, :]
            bpp = region.bpp
            np_buffer = np.frombuffer(buffer, dtype=np.uint8).reshape((layer.height, layer.width, bpp))
            #np_buffer_y = np.swapaxes(np_buffer, 0, 1)
            
            np.savez_compressed('/tmp/test.npz', {1:s}=np_buffer)
            """
        ).format(self._file, layer), timeout_in_seconds=3)
        layer_bg = np.load('/tmp/test.npz')['Background']
        assert np.all(layer_bg[0, 1] == 0)

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
