# Calibration Code For IBM4

this is a working program used with the Itys bitsy m4 to output current from the accompanying current source designed by Rob Sheehan - UCC Physics. It is able to run a self calibration on the then accunt for this in the IBM4. 

## Calibration
Attach a resistor between 10 and 150 Ohms to the output of the current source, then use the IBM4Cal class in Current_Control and run calibration, it will assume the resistor value if 50 Ohms unless specified otherwise, and also assume the calibration is roughly 90 for calculating the range over which to sweep. It will run the different calibrations plot the graph for inspections, if it is good you can choose to save the calibration data to the IBM4, at which point it the calibration will finish and save the data. 
This only needs to be done once solong as the PCB stays the same
If you accidently start the calibration again, it will not write over the previos calibration untill you tell it to

## Current use
still using Current_Control use the Current_Control class to output or sweeps through currents and make what ever funtions you want using them. 
IV plots the voltage over the load with respect to the the current through it 
