* some functions METHOD in the gimp classes can be found in the pdb under gimp-CLASS-METHOD,
  but others not (like Layer.get_pixel_rgn) 
* add a tested set of convenience functions for gimp python scripts that can be imported
* try MkDocs and use a Read the Docs theme for documentation
* use doctest for checking if code within docblocks is working
* functions that modify the file should have a parameter to store the results in a copy of the file instead of inplace
* add readonly mode where modifications can only be saved to another file and not be done in place
* support different datatypes as parameters (int, string, bool, bytes, float) in get_param(name, type)
* add contributors file like https://github.com/parrt/sample-jetbrains-plugin/blob/master/contributors.txt
