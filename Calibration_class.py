import time
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
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
            self.change_times = {}
            self.IBM4_Dict = {}
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    # ------------------------------------------------------------------
    # API
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
            self.run_waveform_sweep_decrease()
            self.run_waveform_sweep_change()

            self.run_current_cal()

            print("Calibration complete. Results:")


        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise


        return dict(self.IBM4_Dict)

    # ------------------------------------------------------------------
    # Internal: validation
    # ------------------------------------------------------------------

    def validate_inputs(self) -> None:
        FUNC_NAME = ".validate_inputs()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            # print("Validating inputs...")
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
            self.the_dev.ZeroIBM4() # ensure outputs are grounded before starting calibration
            time.sleep(0.5) # brief pause to allow hardware to stabilize
            A1_voltage = self.max_v
            A0_values = self.current_limit_calculator(self.resistor, self.k)

            if not A0_values or A0_values[-1] < 0.1:
                raise ValueError("resistor is too large (or approx_k_factor too high); "
                                "max supported A0 is below 0.1 V")
            
            self.the_dev.WriteVoltage('A1', set_voltage =  A1_voltage)
            self.last_time = None
            for A0_voltage in A0_values:
                rt_dict = self.read_waveform_current_change(
                    A0_start=0.0,
                    A0_end=A0_voltage,
                    prefix = "charge_"
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
            self.the_dev.ZeroIBM4() # ensure outputs are grounded before starting calibration
            time.sleep(0.5) # brief pause to allow hardware to stabilize
            A1_voltage = self.max_v

            A0_values = self.current_limit_calculator(self.resistor, self.k)

            self.the_dev.WriteVoltage('A1', set_voltage =  A1_voltage)
            self.last_time = None
            for A0_voltage in A0_values:
                rt_dict = self.read_waveform_current_change(
                    A0_start=A0_voltage,
                    A0_end=0.0,
                    flip=True,
                    prefix = "discharge_"
                )
                self.Discharge_times.update(rt_dict)
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise

    def run_waveform_sweep_change(self) -> None:
        print("Running waveform sweep (change)...")
        """
        Sweep A0 in steps, measure response times, store in self.waveform_plateau_times.
        """
        FUNC_NAME = ".run_waveform_sweep_change()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            self.the_dev.ZeroIBM4() # ensure outputs are grounded before starting calibration
            time.sleep(0.5) # brief pause to allow hardware to stabilize
            A1_voltage = self.max_v

            A0_values = self.current_limit_calculator(self.resistor, self.k)
            A0_range = A0_values[-1]
            no_steps = max(int(A0_range / 0.025), 2)
            A0_10 = np.linspace(0.0, A0_range, no_steps)

            self.the_dev.WriteVoltage('A1', set_voltage =  A1_voltage)
            self.last_time = None
            for i in range(len(A0_10)-1):
                A0_start = A0_10[i]
                A0_end = A0_10[i+1]
                rt_dict = self.read_waveform_current_change(
                    A0_start=A0_start,
                    A0_end=A0_end,
                    prefix = "change_"
                )
                self.change_times.update(rt_dict)
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
    
    # ------------------------------------------------------------------
    # Internal: waveform measurement helpers
    # ------------------------------------------------------------------

    def read_waveform_current_change(
        self,
        A0_start: float,
        A0_end: float,

        flip: bool = False,
        prefix: str = "",
    ):
        """
        Measure current waveform for a given A0 step to zero (change).
        """
        FUNC_NAME = ".read_waveform_current_change()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME

        try:

            key =  f"{prefix}{max(A0_start, A0_end):.2f}"
            time.sleep(0.5)

            Nreads = 2000
            input_ch = "A3"
            self.the_dev.WriteVoltage('A0', set_voltage =  A0_end)
            start = time.time()
            _, _, vals = self.the_dev.ReadVoltage(input_ch, "Multiple Voltage", Nreads)
            end = time.time()

            deltaT = end - start
            measurement_time = deltaT / float(Nreads)
            total_time = measurement_time * Nreads
            times = np.linspace(0, total_time, Nreads)

            smooth_waveform = self.smooth_signal(vals, window_size=200)
            if flip:
                smooth_waveform = -smooth_waveform # upside down for decrease measurement

            _, _, _, response_idx = self.plateau_detection(
                times,
                smooth_waveform,
                A0_voltage=max(A0_start, A0_end)
            )
            
            plateau_time_seconds = (
                times[response_idx]
                if len(times) > response_idx
                else response_idx * measurement_time
            )
            if self.last_time:
                if plateau_time_seconds > self.last_time:
                    plateau_time_seconds = self.last_time
            
            self.last_time = plateau_time_seconds
            
            self.Discharge_times[key] = round(float(plateau_time_seconds), 4)

            return self.Discharge_times
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
        A0_voltage: float = 1.0,
        ):
        FUNC_NAME = ".plateau_detection()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
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
                plt.figure(figsize=(12, 8))
                plt.plot(t, y, label="Measured Signal")
                plt.xlabel("Time (s)")
                plt.ylabel("Voltage (V)")
                plt.title(f"Vin: {A0_voltage} V & A1")

            for start in range(0, n, 250):
                end = min(start + 250, n)
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

                if A0_voltage > 1e-12:
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
                seg1["segment_start"] + int(0.25 * 250),
                seg1["segment_start"] + int(0.5 * 250),
                seg1["segment_start"] + int(0.75 * 250),
                seg1["segment_end"],
                seg2["segment_start"],
                seg2["segment_start"] + int(0.25 * 250),
                seg2["segment_start"] + int(0.5 * 250),
                seg2["segment_start"] + int(0.75 * 250),
                seg2["segment_end"],
                seg3["segment_start"],
                seg3["segment_start"] + int(0.25 * 250),
                seg3["segment_start"] + int(0.5 * 250),
                seg3["segment_start"] + int(0.75 * 250),
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
            else:
                response_idx = seg1["segment_start"]

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

            padded_vals = np.pad(smoothed, pad_width, mode="edge")
            smoothed = np.convolve(padded_vals, kernel, mode="valid")

            return  smoothed[: len(vals)]
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
  
    # ------------------------------------------------------------------
    # Internal: max voltage and CurCal
    # ------------------------------------------------------------------
    def current_limit_calculator(self, resistor: float, approx_k_factor: float):
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

            sweep_data = self.SingleChannelSweep(
                "A0",
                interval,
                v_fixed=A1_voltage,
                waveform_plateau_times = self.IBM4_Dict
            )


            if sweep_data is None or getattr(sweep_data, "size", 0) == 0:
                raise RuntimeError("SingleChannelSweep returned no data; calibration sweep failed")

            ch = 3
            sweep_data[:, ch] = sweep_data[:, ch] * 1000.0 / self.resistor   

            self.cal_factor = np.polyfit(sweep_data[:, 0], sweep_data[:, ch], 1)

            self.IBM4_Dict["cal"] = self.cal_factor[0]
            self.IBM4_Dict["cal_intercept"] = self.cal_factor[1]
            self.IBM4_Dict["r2"] = np.corrcoef(sweep_data[:, 0], sweep_data[:, ch])[0, 1] ** 2
            self.IBM4_Dict["resistor"] = self.resistor
            self.IBM4_Dict["currents_tested"] = [f"{A0 * self.cal_factor[0]}" for A0 in A0_max_list]
            self.IBM4_Dict["help"] = 'use Key = ALL to see saved values' 

            self.IBM4_Dict.update(self.Charge_times)
            self.IBM4_Dict.update(self.Discharge_times)
            self.IBM4_Dict.update(self.change_times)
            

            plt.plot(sweep_data[:, 0], sweep_data[:, ch], "o-")
            plt.plot(
                sweep_data[:, 0],
                self.cal_factor[0] * sweep_data[:, 0] + self.cal_factor[1],
                "r--",
                label=f"Cal_factor = {self.cal_factor[0]:0.2f} mA/V",
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
            
  
            for key, value in self.IBM4_Dict.items():
                print(f"{key}: {value}")

            
            while True:    
                choise = input("Do you want to save the calibration data to IBM4 firmware? (y/n): ").strip().lower()
                if choise == 'y':
                    self.save_dict_to_IBM4(self.IBM4_Dict)
                    break
                elif choise == 'n':
                    print("Calibration data not saved to IBM4 firmware.")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
    
    def SingleChannelSweep(self, swp_channel, voltage_interval:Sweep_Interval.SweepSpace, v_fixed = 0.0, no_averages = 10, waveform_plateau_times = None):
    
        """
        Enable the microcontroller to perform a linear sweep of measurements using a single channel
        start at v_strt, set voltage, read inputs, increment_voltage, return voltage readings at all inputs
        format the voltage readings after the fact
    
        swp_channel is the channel being used as a voltage source
        voltage_interval describes the voltage sweep space
        v_fixed is the constant voltage to be output by the channel that is NOT being swept
        caveat emptor no_steps is constrained by fact that smallest voltage increment is 0.01V

        Output is a numpy array of the form
        [v_set, A2, A3, A4, A5, D2]
        """

        self.FUNC_NAME = ".SingleChannelSweep()" # use this in exception handling messages
        self.ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + self.FUNC_NAME

        try:       

            # Set the voltage on the channel that is NOT sweeping
            fixed_channel = 'A1' if swp_channel == 'A0' else 'A0'
            self.the_dev.WriteVoltage(fixed_channel, v_fixed)
            # Proceed with the single channel linear voltage sweep


            voltage_data = np.array([]) # instantiate an empty numpy array to store the sweep data
            v_set = voltage_interval.start # initialise the set-voltage
            count = 0
            #while v_set < voltage_interval.stop:

            copy = None
            for i in range(0, voltage_interval.Nsteps, 1):
                step_data = np.array([]) # instantiate an empty numpy array to hold the data for each step of the sweep
                self.the_dev.WriteVoltage(swp_channel, v_set) # set the voltage at the analog output channel

                delay_seconds = 0.1
                plateau_key = None
                if isinstance(waveform_plateau_times, dict) and len(waveform_plateau_times) > 0:
                    numeric_keys = [key for key in waveform_plateau_times if isinstance(key, (int, float))]
                    plateau_key = min((key for key in numeric_keys if key > v_set), default=None)
                    if plateau_key is not None:
                        candidate_delay = waveform_plateau_times.get(plateau_key)
                        if isinstance(candidate_delay, (int, float)) and candidate_delay >= 0.0:
                            delay_seconds = candidate_delay

                time.sleep(delay_seconds)
                if copy is None or copy != delay_seconds:
                    print(f'{v_set:.4f} V - delay of {delay_seconds:.2f} seconds ')
                copy = delay_seconds

                chnnl_values = self.the_dev.ReadAverageVoltageAllChnnl(no_averages) # read the averaged voltages at all analog input channels
                # save the data
                step_data = np.append(step_data, v_set) # store the set-voltage value for this step
                step_data = np.append(step_data, chnnl_values) # store the  measured voltage values from all channels for this step
                # store the  set-voltage and the measured voltage values from all channels for this step
                # use append on the first step to initialise the voltage_data array
                # use vstack on subsequent steps to build up the 2D array of data
                voltage_data = np.append(voltage_data, step_data) if count == 0 else np.vstack([voltage_data, step_data])
                v_set = v_set + voltage_interval.delta # increment the set-voltage
                count = count + 1 if count == 0 else count # only need to increment count once to build up the array
            print('Sweep complete')
            self.the_dev.ZeroIBM4() # ground the analog outputs
            return voltage_data
         
        except Exception as e:
            print(self.ERR_STATEMENT)
            print(e)   
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
            dev.send_mes(msg=msg_payload, loud=True)
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
        if self.the_dev is None:
            self.the_dev = IBM4_Lib.Ser_Iface()
        try:
            response = self.the_dev.Read_Cal_from_IBM4(key=key)
            print(response)
            return response
        finally:
            if self.the_dev is not None:
                del self.the_dev



class Output_current:
    
    MOD_NAME_STR = "IBM4_Lib"
    FUNC_NAME = ".Ser_Iface()" # use this in exception handling messages
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    IBM4Port = None
    instr_obj = None

    def __init__(self):
        self.currnet = 0.0
        self.max_voltage = 3.3
        self.the_dev = IBM4_Lib.Ser_Iface()


    def set_voltage(self, voltage):
        self.the_dev.WriteVoltage('A1', set_voltage =  self.max_voltage)

    def validate_current_input(self) -> None:
        FUNC_NAME = ".validate_current_input()"
        ERR_STATEMENT = "Error: " + self.MOD_NAME_STR + FUNC_NAME
        try:
            if self.resistor <= 0.0:
                raise ValueError("resistor must be > 0 Ohm")
            if not (0.0 < self.max_v <= 3.3):
                raise ValueError("max_voltage_over_component must be in (0, 3.3] V")
            if self.k <= 0.0:
                raise ValueError("approx_k_factor must be > 0")
        except Exception as e:
            print(f"{ERR_STATEMENT}: {e}")
            raise
