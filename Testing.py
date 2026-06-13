from Calibration_class import Current_Control 


Current_Control = Current_Control()

# Current_Control.set_current(Current=100, Max_V=3.3)
Current_Control.sweep_current(Max_V=3.3, start=0, end=100, steps=10) 