import Calibration_class


cal_clas = Calibration_class.IBM4Calibrator(show_plots=True)

cal_clas.calibrate()
# test = {"a": 1, "b": 2}
# cal_clas.save_dict_to_IBM4(test)
cal_clas.get_cal()

