from Calibration_class import IBM4Calibrator
import Control_Examples
Cal = IBM4Calibrator(show_plots=False)

# Cal.calibrate()
print("\n\n")
Cal.Get_saved_values("0.1")
print("\n\n")
