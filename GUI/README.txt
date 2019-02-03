#################################
USEFUL NOTES FOR TETHERS GUI
Created on: 2019-01-22
Author: Nicola and Anjalie
#################################

Bugs/things that could be improved:
- NOTE: current version assumes image is .tif file and output has to be pickle file
- make exe
<<<<<<< HEAD
- SOLVED: make 3D plot also with phase dependent option
- SOLVED: Add guides when plotting midline? 
- SOLVED: Slow when working with big files (duh..): it's actually the 3D plot!
- SOLVED: saving, make notice of ".p" or make it automatic
- SOLVED: Showing multiple channels is not as nice as in FIJI (transparency?)
- SOLVED: b&c settings of channel 0 should be remembered when moving to channel 1 and back
- SOLVED: Possible to make the AVCanal point red? I've already made the mistake of making the midline with the AVC selection
- SOLVED: Possible to indicate z plane max and contraction phase max?
=======
- implement click delay (0.5 sec?) to prevent double overlapping points
- solve error message when closing dimensiondefiner window with X
- use same color/marker for analysis scripts as for GUI
>>>>>>> dev_branch

Documentation:
- open terminal in the folder where "source_GUI.py" is and type ">> python source_GUI.py" to launch the application
- "Load Image data" is the only button available. Gives a Error message when a non 'tif' file is selected
- IMPORTANT: you should have a midline in every contraction phase where you labeled tethers, AND you should have 1 and only 1 AVCanal!

