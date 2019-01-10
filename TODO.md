* add contributors file like https://github.com/parrt/sample-jetbrains-plugin/blob/master/contributors.txt
** own the copyright, do not share -> makes it easier to switch license or to decide other things
* write tutorial
* GimpFileCollection
** add examples to documentation
** replace file prefix pgimp.GimpFileCollection.GimpFileCollection#replace_path_components as well, not only path prefix and file suffix
* newtype handling in pgimp.GimpFile.GimpFile#add_layer_from_file; copy mode, opacity and type from source layer unless specified otherwise
* gimp file + collection: rename, reorder layer functionality
* describe how to use docker compose build environment in pycharm
* gimp exports gray image to png graya even though there is no need for that: save gray and rgb images without alpha when exporting to png
* pgimp.GimpFile.GimpFile#add_layer_from_file: add_layer_from_gimp_file, add_layer_from_file
* pgimp.gimp.layer.add_layer_from_file: currently only first layer is copied but when the image has multiple layers it would be more safe to merge visible layers
