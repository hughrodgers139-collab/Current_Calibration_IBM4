from Calibration_class import IBM4Calibrator
import time
Cal = IBM4Calibrator(show_plots=False)
print("\n")
start = time.time()
Cal.calibrate()
end = time.time()
diff = end - start
print(diff)
