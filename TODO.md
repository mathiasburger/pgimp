* newtype handling in pgimp.GimpFile.GimpFile#add_layer_from_file; copy mode, opacity and type from source layer unless specified otherwise
* gimp file + collection: rename, reorder layer functionality
* describe how to use docker compose build environment in pycharm
* gimp exports gray image to png graya even though there is no need for that: save gray and rgb images without alpha when exporting to png
* pgimp.GimpFile.GimpFile#add_layer_from_file: add_layer_from_gimp_file, add_layer_from_file
* pgimp.gimp.layer.add_layer_from_file: currently only first layer is copied but when the image has multiple layers it would be more safe to merge visible layers
* do not rely on stdout and stderr anymore, use files to communicate
  because gimp likes to pollute stdout and stderr unpredictably
