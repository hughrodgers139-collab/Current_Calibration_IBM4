from Calibration_class import Current_Control 

Current_Control = Current_Control()

# Current_Control.Current(Current=2.0, Max_V=3.1)
# Current_Control.other_sweep_current(Max_V=3.1, start=0, end=40, steps=100, Min_delay=0.1)
# Current_Control.IV_diagram(Max_V=3.3, start=0, end=40, steps=100, Min_delay=0.1)
Current_Control.Get_saved_values("charge") 