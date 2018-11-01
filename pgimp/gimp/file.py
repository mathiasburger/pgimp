import gimp


def open_xcf(filename):
    return gimp.pdb.gimp_xcf_load(0, filename, filename)


def save_xcf(image, filename):
    gimp.pdb.gimp_xcf_save(0, image, None, filename, filename)
