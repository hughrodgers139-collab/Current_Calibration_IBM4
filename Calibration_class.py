import time
import numpy as np
import matplotlib.pyplot as plt
import IBM4_Lib
import Sweep_Interval

class IBM4Calibrator:
    """
    Integrated current calibration class for IBM4.

    Responsibilities:
    - Validate inputs (resistor, voltage limits, k-factor)
    - Open/close IBM4 device
    - Run current calibration sweeps (CurCal)
    - Measure waveforms (increase/decrease)
    - Detect plateau via segment regressions
    - Smooth signals
    - Compute max supported A0 voltages
    - Save/load calibration data to/from IBM4 firmware
    """
    
    MOD_NAME_STR = "IBM4_Lib"
    FUNC_NAME = ".Ser_Iface()" # use this in exception handling messages
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    IBM4Port = None
    instr_obj = None

    def __init__(
        self,
        resistor: float = 50.0,
        max_voltage_over_component: float = 3.3,
        approx_k_factor: float = 90.0,
        show_plots: bool = False,
    ):
        FUNC_NAME = ".__init__()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME  
        try:
            self.resistor = float(resistor)
            self.max_v = float(max_voltage_over_component)
            self.k = float(approx_k_factor)
            self.show_plots = show_plots 

            self.validate_inputs()

            # Open device once
            self.the_dev = IBM4_Lib.Ser_Iface()
            self.Charge_times = {}
            self.Discharge_times = {}
            self.waveform_plateau_times = {}
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
        finally:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calibrate(self) -> dict:
        print("Starting calibration process...")
        """
        High-level calibration entry point.
        Performs waveform-based response-time measurement,
        then runs CurCal to compute calibration factor and save results.
        """
            
        FUNC_NAME = ".calibrate()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            self.run_waveform_sweep_increase()
            self.waveform_plateau_times["Increase"] = self.Charge_times

            self.run_waveform_sweep_decrease()
            self.waveform_plateau_times["Decrease"] = self.Discharge_times

            self.run_current_cal()

            print("\n=== Charge Times (A0 → plateau) ===")
            for k, v in sorted(self.Charge_times.items()):
                print(f"A0 = {k:.4f} V  →  Charge time = {v:.6f} s")

            print("\n=== Discharge Times (plateau → 0) ===")
            for k, v in sorted(self.Discharge_times.items()):
                print(f"A0 = {k:.4f} V  →  Discharge time = {v:.6f} s")
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise


        return dict(self.waveform_plateau_times)

    # ------------------------------------------------------------------
    # Internal: validation
    # ------------------------------------------------------------------

    def validate_inputs(self) -> None:
        FUNC_NAME = ".validate_inputs()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            print("Validating inputs...")
            if self.resistor <= 0.0:
                raise ValueError("resistor must be > 0 Ohm")
            if not (0.0 < self.max_v <= 3.3):
                raise ValueError("max_voltage_over_component must be in (0, 3.3] V")
            if self.k <= 0.0:
                raise ValueError("approx_k_factor must be > 0")
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    # ------------------------------------------------------------------
    # Internal: waveform sweeps
    # ------------------------------------------------------------------

    def run_waveform_sweep_increase(self) -> None:
        print("Running waveform sweep for current increase...")
        """
        Sweep A0 upwards, measure response times, store in self.waveform_plateau_times.
        """

        FUNC_NAME = ".run_waveform_sweep_increase()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            A1_voltage = self.max_v
            A0_values = self.current_limit_calculator(self.resistor, self.k)

            if not A0_values or A0_values[-1] < 0.1:
                raise ValueError("resistor is too large (or approx_k_factor too high); "
                                "max supported A0 is below 0.1 V")
            
            self.the_dev.WriteVoltage('A1', set_voltage =  A1_voltage)

            for A0_voltage in A0_values:
                rt_dict = self.read_waveform_current_increase(
                    A0_voltage=A0_voltage,
                    Charge_times=self.Charge_times,
                )
                self.Charge_times.update(rt_dict)
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    def run_waveform_sweep_decrease(self) -> None:
        print("Running waveform sweep (decrease)...")
        """
        Sweep A0 downwards, measure response times, store in self.waveform_plateau_times.
        """
        FUNC_NAME = ".run_waveform_sweep_decrease()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            A1_voltage = self.max_v

            A0_values = self.current_limit_calculator(self.resistor, self.k)

            self.the_dev.WriteVoltage('A1', set_voltage =  A1_voltage)

            for A0_voltage in A0_values:
                rt_dict = self.read_waveform_current_decrease(
                    A0_voltage=A0_voltage,
                    Discharge_times=self.Discharge_times,
                )
                self.Discharge_times.update(rt_dict)
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    # ------------------------------------------------------------------
    # Internal: waveform measurement helpers
    # ------------------------------------------------------------------

    def read_waveform_current_increase(
        self,
        A0_voltage: float,
        Charge_times: dict | None = None,
        ) -> dict:
        FUNC_NAME = ".read_waveform_current_increase()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            print(f"Measuring increase waveform for A0={A0_voltage} V...")
            """
            Measure current waveform for a given A0 step from zero (increase).
            """
            if Charge_times is None or not isinstance(Charge_times, dict):
                Charge_times = {}

            Nreads = 5000
            input_ch = "A3"


            self.the_dev.WriteVoltage('A0', set_voltage =  0)
            time.sleep(0.5)

            # Step both A0 and A1
            self.the_dev.WriteVoltage('A0', set_voltage =  A0_voltage)
 

            start = time.time()
            _, _, vals = self.the_dev.ReadVoltage(input_ch, "Multiple Voltage", Nreads)
            end = time.time()

            deltaT = end - start
            measurement_time = deltaT / float(Nreads)
            total_time = measurement_time * Nreads
            times = np.linspace(0, total_time, Nreads)

            smooth_waveform = self.smooth_signal(vals, window_size=200)

            _, _, _, response_idx = self.plateau_detection(
                times,
                smooth_waveform,
                segment_length=250,
                A0_voltage=A0_voltage,
            )

            plateau_time_seconds = (
                times[response_idx]
                if len(times) > response_idx
                else response_idx * measurement_time
            )

            voltage_key = round(float(A0_voltage), 4)
            Charge_times[voltage_key] = round(float(plateau_time_seconds), 4)

            return Charge_times
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    def read_waveform_current_decrease(
        self,
        A0_voltage: float,
        Discharge_times: dict | None = None,
        Charge_times: dict | None = None,
    ):
        # Ensure Charge_times is valid
        if Charge_times is None:
            Charge_times = self.Charge_times

        if Discharge_times is None:
            Discharge_times = self.Discharge_times

        """
        Measure current waveform for a given A0 step to zero (decrease).
        """
        FUNC_NAME = ".read_waveform_current_decrease()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME

        try:
            self.the_dev.WriteVoltage('A0', set_voltage =  A0_voltage)
            
            key = f"{A0_voltage:.4f}"
            delay = Charge_times.get(key, 0.0)
            time.sleep(delay+1)


    
            print(f"Measuring decrease waveform for A0={A0_voltage} V...")

            if Discharge_times is None or not isinstance(Discharge_times, dict):
                Discharge_times = {} 

            Nreads = 5000
            input_ch = "A3"
            self.the_dev.WriteVoltage('A0', set_voltage =  0)
            start = time.time()
            avg, err, vals = self.the_dev.ReadVoltage(input_ch, "Multiple Voltage", Nreads)
            end = time.time()

            deltaT = end - start
            measurement_time = deltaT / float(Nreads)
            total_time = measurement_time * Nreads
            times = np.linspace(0, total_time, Nreads)

            smooth_waveform = self.smooth_signal(vals, window_size=200)
            smooth_waveform = -smooth_waveform
            _, _, _, response_idx = self.plateau_detection(
                times,
                smooth_waveform,
                segment_length=250,
                A0_voltage=A0_voltage
            )

            plateau_time_seconds = (
                times[response_idx]
                if len(times) > response_idx
                else response_idx * measurement_time
            )

            voltage_key = round(float(A0_voltage), 4)
            Discharge_times[voltage_key] = round(float(plateau_time_seconds), 4)

            return Discharge_times
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    # ------------------------------------------------------------------
    # Internal: plateau detection & smoothing
    # ------------------------------------------------------------------

    def plateau_detection(
        self,
        times,
        values,
        segment_length: int = 250,
        A0_voltage: float = 1.0,
        ):
        FUNC_NAME = ".plateau_detection()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            print("Performing plateau detection on waveform...")
            """
            Detect plateau by performing linear regression on segments and
            finding where the slope becomes sufficiently small.
            Returns (results, slope_values, candidates, response_idx).
            """
            results = []
            slope_values = []
            candidates = []
            response_time = 0

            t = np.asarray(times)
            y = np.asarray(values)
            n = len(t)

            if n == 0 or len(y) == 0:
                return results, slope_values, candidates, response_time

            tolerance = 0.01

            if self.show_plots:
                plt.figure(figsize=(10, 6))
                plt.xlabel("Time (s)")
                plt.ylabel("Voltage (V)")
                plt.title(f"Vin: {A0_voltage} V & A1")

            for start in range(0, n, segment_length):
                end = min(start + segment_length, n)
                t_seg = t[start:end]
                y_seg = y[start:end]

                if len(t_seg) <= 4:
                    continue

                t_mean = t_seg.mean()
                y_mean = y_seg.mean()

                cov = np.sum((t_seg - t_mean) * (y_seg - y_mean))
                var = np.sum((t_seg - t_mean) ** 2)

                if var == 0:
                    slope = 0.0
                    intercept = y_mean
                    y_pred = np.full_like(t_seg, fill_value=y_mean, dtype=float)
                else:
                    slope = cov / var
                    intercept = y_mean - slope * t_mean
                    y_pred = slope * t_seg + intercept

                results.append(
                    {
                        "segment_start": start,
                        "segment_end": end - 1,
                        "slope": slope,
                        "intercept": intercept,
                    }
                )

                if self.show_plots:
                    plt.plot(t_seg, y_seg, "o")
                    plt.plot(t_seg, y_pred, "r--")

                if abs(A0_voltage) > 1e-12:
                    slope_values.append(slope / A0_voltage)
                else:
                    slope_values.append(slope)

            if len(results) == 0 or len(slope_values) == 0:
                return results, slope_values, candidates, response_time

            max_slope_segment = max(range(len(slope_values)), key=lambda i: slope_values[i])
            s1 = min(max_slope_segment + 1, len(results) - 1)
            s2 = min(max_slope_segment + 2, len(results) - 1)
            s3 = min(max_slope_segment + 3, len(results) - 1)

            seg1 = results[s1]
            seg2 = results[s2]
            seg3 = results[s3]

            stable_point = y[seg3["segment_end"]]

            candidates = [
                seg1["segment_start"],
                seg1["segment_start"] + int(0.25 * segment_length),
                seg1["segment_start"] + int(0.5 * segment_length),
                seg1["segment_start"] + int(0.75 * segment_length),
                seg1["segment_end"],
                seg2["segment_start"],
                seg2["segment_start"] + int(0.25 * segment_length),
                seg2["segment_start"] + int(0.5 * segment_length),
                seg2["segment_start"] + int(0.75 * segment_length),
                seg2["segment_end"],
                seg3["segment_start"],
                seg3["segment_start"] + int(0.25 * segment_length),
                seg3["segment_start"] + int(0.5 * segment_length),
                seg3["segment_start"] + int(0.75 * segment_length),
                seg3["segment_end"],
            ]

            i = 0
            response_idx = None

            while i < len(candidates):
                idx = candidates[i]
                idx = min(max(0, idx), len(y) - 1)
                if stable_point == 0:
                    close_enough = abs(y[idx] - stable_point) < tolerance
                else:
                    close_enough = abs(y[idx] - stable_point) / abs(stable_point) < tolerance

                if close_enough:
                    response_idx = idx
                    break
                i += 1

            if response_idx is None:
                response_idx = seg3["segment_end"]

            if self.show_plots:
                plt.axvline(
                    x=t[response_idx],
                    color="g",
                    linestyle="--",
                    label=f"Response Time: {t[response_idx]:.4f} s",
                )
                plt.legend()
                plt.show()

            return results, slope_values, candidates, response_idx
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    def smooth_signal(self, vals, window_size: int):
        """
        Apply a moving average to smooth the signal.
        """
        FUNC_NAME = ".smooth_signal()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            kernel = np.ones(window_size) / window_size
            pad_width = window_size // 2

            padded_vals = np.pad(vals, pad_width, mode="edge")
            smoothed = np.convolve(padded_vals, kernel, mode="valid")

            return  smoothed[: len(vals)]
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
  
    # ------------------------------------------------------------------
    # Internal: max voltage and CurCal
    # ------------------------------------------------------------------

    def current_limit_calculator(self, resistor: float, approx_k_factor: float):
        print("Computing max supported A0 voltages based on resistor and k-factor...")
        """
        Compute allowed A0 voltages based on resistor and k-factor.
        """
        FUNC_NAME = ".current_limit_calculator()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            A0 = [0.02,
                0.03,
                0.06,
                0.1,
                0.3,
                0.5,
                1.0,
                1.3,
                1.5,
                2.0,
                2.3,
                2.5,
                3.0,
                3.3
                ]
            
            return [
                v
                for v in A0
                if v <= 3.3 / resistor / (approx_k_factor / 1000.0) and v * approx_k_factor <= 250
            ]
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    def run_current_cal(self) -> None:
        print("Running current calibration sweep...")
        """
        Perform current calibration sweep (CurCal) using plateau times.
        """
        FUNC_NAME = ".run_current_cal()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            A0_min = 0.0
            A1_voltage = self.max_v

            A0_max_list = self.current_limit_calculator(self.resistor, self.k)
            if not A0_max_list:
                raise ValueError("No valid A0_max found for given resistor and k-factor")
            A0_max = A0_max_list[-1]

            if A0_max < 0.05:
                raise ValueError("resistor is too large assuming approx_k_factor of 90")

            no_steps = max(int(A0_max / 0.01), 2)
            interval = Sweep_Interval.SweepSpace(no_steps, A0_min, A0_max)

            sweep_data = self.the_dev.SingleChannelSweepC(
                "A0",
                interval,
                v_fixed=A1_voltage,
                resistor=self.resistor,
                waveform_plataue_times=self.waveform_plateau_times,
            )


            if sweep_data is None or getattr(sweep_data, "size", 0) == 0:
                raise RuntimeError("SingleChannelSweepC returned no data; calibration sweep failed")

            ch = 3
            sweep_data[:, ch] = sweep_data[:, ch] * 1000.0 / self.resistor  # convert to mA

            cal_factor = np.polyfit(sweep_data[:, 0], sweep_data[:, ch], 1)
            self.waveform_plateau_times["Cal"] = cal_factor[0]
            self.waveform_plateau_times["Cal_intercept"] = cal_factor[1]
            self.waveform_plateau_times["R2"] = np.corrcoef(sweep_data[:, 0], sweep_data[:, ch])[0, 1] ** 2
            self.waveform_plateau_times["resistor"] = self.resistor

            plt.plot(sweep_data[:, 0], sweep_data[:, ch], "o-")
            plt.plot(
                sweep_data[:, 0],
                cal_factor[0] * sweep_data[:, 0] + cal_factor[1],
                "r--",
                label=f"Cal_factor = {cal_factor[0]:0.2f} mA/V",
            )
            plt.xlabel("Voltage (mV)")
            plt.ylabel("Current (mA)")
            plt.legend()
            plt.title("Current Calibration")
            plt.text(
                0.5,
                0.9,
                f"resistor = {self.resistor:0.1f} Ohm",
                transform=plt.gca().transAxes,
                ha="center",
            )
            plt.show()
            
            self.waveform_plateau_times["Current_times"] = A0_max_list
            #__________________________________________________________________________________________________________________________________________________________________________________________

            self.waveform_plateau_times["help"] = '"Cal" for calibration factor in mA/V\n "Cal_intercept" for intercept in mA, \n "R2" for R-squared,\n "resistor" for sense resistor.'  # noqa: E501
            
            #__________________________________________________________________________________________________________________________________________________________________________________________
            while True:    
                choise = input("Do you want to save the calibration data to IBM4 firmware? (y/n): ").strip().lower()
                if choise == 'y':
                    self.save_dict_to_IBM4(self.waveform_plateau_times)
                    break
                elif choise == 'n':
                    print("Calibration data not saved to IBM4 firmware.")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
               
    # ------------------------------------------------------------------
    # Internal: save/load to IBM4
    # ------------------------------------------------------------------

    def save_dict_to_IBM4(self, msg_payload=None) -> None:
        """
        Send a message payload to the IBM4 firmware.
        """        
        FUNC_NAME = ".save_dict_to_IBM4()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        print("Saving calibration data to IBM4 firmware...")
        local_dev = None
        try:
            if self.the_dev is None:
                local_dev = IBM4_Lib.Ser_Iface()
                dev = local_dev
            else:
                dev = self.the_dev
            dev.send_mes(msg=msg_payload)
        finally:
            if local_dev is not None:
                del local_dev

    def Get_saved_values(self, key: str | None = None):
        print("Retrieving calibration data from IBM4...")
        """
        Get saved calibration from IBM4 firmware.
        """
        FUNC_NAME = ".Get_saved_values()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        the_dev = IBM4_Lib.Ser_Iface()
        try:
            response = the_dev.Get_Cal_from_IBM4(key=key)
            print(response)
            return response
        finally:
            if the_dev is not None:
                del the_dev
