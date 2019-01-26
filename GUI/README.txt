#################################
USEFUL NOTES FOR TETHERS GUI
Created on: 2019-01-22
Author: Nicola and Anjalie
#################################

Bugs/things that could be improved:
- NOTE: current version assumes image dimension is ALWAYS 512(H)x1024(W) and .tif file and pickle file
- make exe
- SOLVED: make 3D plot also with phase dependent option
- SOLVED: Add guides when plotting midline? 
- SOLVED: Slow when working with big files (duh..): it's actually the 3D plot!
- SOLVED: saving, make notice of ".p" or make it automatic
- SOLVED: Showing multiple channels is not as nice as in FIJI (transparency?)
- SOLVED: b&c settings of channel 0 should be remembered when moving to channel 1 and back

Documentation:
- open terminal in the folder where "source_GUI.py" is and type ">> python source_GUI.py" to launch the application
- "Load Image data" is the only button available. Gives a Error message when a non 'tif' file is selected
- IMPORTANT: you should have a midline in every contraction phase where you labeled tethers, AND you should have 1 and only 1 AVCanal!

