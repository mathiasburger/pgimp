* add a tested set of convenience functions for gimp python scripts that can be imported
* add contributors file like https://github.com/parrt/sample-jetbrains-plugin/blob/master/contributors.txt
* write tutorial
* GimpFileCollection
** Add or merge layers using another collection
** add examples to documentation
* newtype handling in pgimp.GimpFile.GimpFile#add_layer_from_file; copy mode, opacity and type from source layer unless specified otherwise
* implement class hierarchy in generated documentation, get base class like this: inspect.getmro(gimp.Layer)[1].__name__
