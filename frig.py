resistor = 50

calibration_factor = 90


def max_voltage(resistor, calibration_factor):
    A0 = [0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25] 

    A0 = [v for v in A0 if v <=  3.3/resistor /(calibration_factor/1000) and v * calibration_factor <= 250]
    return A0

print("\nA0 voltage: ", max(max_voltage(resistor, calibration_factor)), "\n")