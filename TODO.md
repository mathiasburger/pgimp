* add contributors file like https://github.com/parrt/sample-jetbrains-plugin/blob/master/contributors.txt
** own the copyright, do not share -> makes it easier to switch license or to decide other things
* write tutorial
* GimpFileCollection
** add examples to documentation
** replace file prefix pgimp.GimpFileCollection.GimpFileCollection#replace_path_components as well, not only path prefix and file suffix
* newtype handling in pgimp.GimpFile.GimpFile#add_layer_from_file; copy mode, opacity and type from source layer unless specified otherwise
* gimp file + collection: rename, reorder layer functionality
* use find_packages from setuptools instead of listing packages manually
* why does pgimp fail on deep learning machine?
* why is only the toplevel package installed?
* test installation in conda environment.yml:
  - pip:
    - "git+https://github.com/mabu-github/pgimp"
