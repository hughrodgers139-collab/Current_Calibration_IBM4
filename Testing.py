"""
Script for running the Methods from Control_Examples.py
Uncomment the method you would like to test

R. Sheehan 19 - 9 - 2024
"""

import os
import Control_Examples

# Where are you? 
pwd = os.getcwd()

# print(pwd)


# 0. Basic Find, Open, Close
# Control_Examples.Simple_Open_Close()

# 1. Step through voltages
#Control_Examples.Step_Through_Voltages()

# 2. Basic single channel sweep
#Control_Examples.Simple_Sweep()

# 3. Read all input channels
#Control_Examples.Simple_Sweep_Read_All()

# 4. Differential read
#Control_Examples.Differential_Readings()

# 5. Multi-reads and timings
#Control_Examples.Multiple_Readings()

# 6. Multimeter mode
# Control_Examples.Multimeter_Mode()

# 7. Linear single channel sweep
# Control_Examples.Linear_Sweep_V1()
# Control_Examples.Linear_Sweep_V2()

# Control_Examples.CurCal()

Dict = {
    "key1": "1",
}

# Control_Examples.Read_Current_waveform(no_reads=100)
# Control_Examples.send_message(Dict)
# Control_Examples.Echo(Key = "key1")
times, samples = Control_Examples.Read_Current_waveform(no_reads=100, delay=0.0005)
import matplotlib.pyplot as plt

if times is not None and samples is not None:
    n = min(len(times), len(samples))
    if n > 0:
        t_plot = times[:n]
        y_plot = samples[:n]
        plt.plot(t_plot, y_plot)
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        plt.title("Vin3 Waveform vs Time")
        plt.show()

