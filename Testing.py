"""
Script for running the Methods from Control_Examples.py
Uncomment the method you would like to test

R. Sheehan 19 - 9 - 2024
"""

import os
import Control_Examples as CE

import numpy
import matplotlib.pyplot as plt
import json
import ast
# Where are you? 
pwd = os.getcwd()
"""
# print(pwd)

# 0. Basic Find, Open, Close
# CE.Simple_Open_Close()

# 1. Step through voltages
#CE.Step_Through_Voltages()

# 2. Basic single channel sweep
# CE.Simple_Sweep()

# 3. Read all input channels
# CE.Simple_Sweep_Read_All()

# 4. Differential read
# CE.Differential_Readings()

# 5. Multi-reads and timings
# CE.Multiple_Readings()

# 6. Multimeter mode
# CE.Multimeter_Mode()

# 7. Linear single channel sweep
# CE.Linear_Sweep_V1()
# CE.Linear_Sweep_V2()
"""

CE.calibrate(resistor = 10, show_plots = False)
 
CE.Get_cal("help")

print("\n")

