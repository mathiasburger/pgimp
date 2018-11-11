import gimp


def open_xcf(filename):
    """
    :type filename: str
    :rtype: gimp.Image
    """
    return gimp.pdb.gimp_xcf_load(0, filename, filename)


def save_xcf(image, filename):
    """
    :param image: gimp.Image
    :param filename: str
    """
    gimp.pdb.gimp_xcf_save(0, image, None, filename, filename)
