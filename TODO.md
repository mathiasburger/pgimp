* some functions METHOD in the gimp classes can be found in the pdb under gimp-CLASS-METHOD,
  but others not (like Layer.get_pixel_rgn) 
* copy layer from one image to another
* insert layer before/after layer name
* remove layer name
* long running gimp scripts (stream for stdout, stderr)
* add layer with position/index
* add a tested set of convenience functions for gimp python scripts that can be imported
  (import needs to look within the package)
* create INDEXED images (8bit + colormap), search for "palette" functions in gimp
* try shpinx for documentation and doctest for checking if code within docblocks is working
* functions that modify the file should have a parameter to store the results in a copy of the file instead of inplace
* add readonly mode where modifications can only be saved to another file and not be done in place
* support different datatypes as parameters (int, string, bool, bytes, float) in get_param(name, type)
* add library of convenience functions that can be imported

