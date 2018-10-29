* remove parameter run_mode from pdb routines
* some functions METHOD in the gimp classes can be found in the pdb under gimp-CLASS-METHOD,
  but others not (like Layer.get_pixel_rgn) 
* try importing the script to execute after the initializer to get proper line numbers of a file when something 
  goes wrong instead of only having linenumbers of stdin which also contains the initializer
* copy layer from one image to another
