# Current_Calibration_IBM4

Automaticaly calibrates current source attached to ItsyBitsyM4.
This is currentely running the computer attached to the IBM4, Later versions should include it in the firmware of the IBM4 but as this is prototyping the main code segmanets that are used can be found as a function in Controle_Examples.py.

It is currently able to measure the wave form as teh current source comes to the correct output current, this gives us a measurement of how long it should take to go from zero to a set current.
this can later be implimented in a new function Current(), which will allow us to set the IBM4 and PCB to output a set value curretent.
It has been found that the time takent to reach the curretn is relativly independent of max voltage set by channel A1, which makes sense. 
This still needs to be updated to measure the time taken to hope from a non zero current to a larger and smaller current, however this may not be nesisary in the final calibration


The calibration factor is currently made but will requires us to have the function Current() first so it is able to reliable set the currents 

