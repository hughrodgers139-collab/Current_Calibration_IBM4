from Current_Control import Current_Control 
from Current_Control import IBM4Cal

# IBM4Cal = IBM4Cal()
# IBM4Cal.calibrate()


Current_Control = Current_Control()

Current_Control.Just_Current(Current=20, Max_V=3.3, delay = 1)
Current_Control.IV_diagram(Max_V=3.3, start=40, end=0, steps=40, Min_delay=0)
