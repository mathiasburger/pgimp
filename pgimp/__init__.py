PROJECT = 'pgimp'
AUTHOR = 'Mathias Burger'
__version__ = '1.0.0-alpha-17'

execute_scripts_with_process_check = True
""" 
Must not be changed after GimpScriptRunner was imported.

The mechanism removes the dependency on psutil during installation because it cannot 
be guaranteed that psutil is already present in the python environment.
"""
