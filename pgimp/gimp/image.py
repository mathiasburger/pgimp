from pgimp.gimp.file import open_xcf, close_image, save_xcf


class XcfImage:
    def __init__(self, file, save=False):
        """
        :type file: str
        :type save: bool
        """
        self._file = file
        self._save = save
        self._image = None

    def __enter__(self):
        self._image = open_xcf(self._file)
        return self._image

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._save:
            save_xcf(self._image, self._file)
        close_image(self._image)
        return False
