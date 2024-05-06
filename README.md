# 3dResume
python script to resume 3d printing
## you need your original gcode, and you need to find your current printing layer
## the generated gcode will heat the Extruder to your set temperature, 
## then lift 2mm
## then home x/y z
## then clean the Extruder 
make sure your model is not too big, the Extruder might bump into it if the model is too big, then you need to avoid this step
## then resume z x/y e


