from Current_Control import Current_Control 
from Current_Control import IBM4Cal

# IBM4Cal = IBM4Cal()
# IBM4Cal.calibrate()


Current_Control = Current_Control()

# Current_Control.Just_Current(Current=20, Max_V=3.3, delay = 1)
# Current_Control.other_sweep_current(Max_V=3.1, start=0, end=40, steps=100, Min_delay=0.1)
Current_Control.IV_diagram(Max_V=3.3, start=40, end=0, steps=10000, Min_delay=0)
# Current_Control.Get_saved_values("charge") 
