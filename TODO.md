* add a tested set of convenience functions for gimp python scripts that can be imported
* try sphinx for documentation
* use doctest for checking if code within docblocks is working
* functions that modify the file should have a parameter to store the results in a copy of the file instead of inplace
* add readonly mode where modifications can only be saved to another file and not be done in place
* add contributors file like https://github.com/parrt/sample-jetbrains-plugin/blob/master/contributors.txt
* document parameters of pgimp.GimpScriptRunner.GimpScriptRunner#execute and other execute* parameters that are additional to the ones in execute()
* add create empty image method create_empty() in GimpFile
* document that numpy arrays are y,x indexed
* find out if certain blocks of text can be copied between docblocks using sphinx functionality
  and use it to add notes about numpy uint8 and row-major order (yx instead of xy)
