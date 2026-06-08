import time
import numpy as np
import matplotlib.pyplot as plt
import IBM4_Lib
import Sweep_Interval
import Control_Examples

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

    def __init__(
        self,
        resistor: float = 50.0,
        max_voltage_over_component: float = 3.25,
        approx_k_factor: float = 90.0,
        show_plots: bool = False,
    ):
        self.resistor = float(resistor)
        self.max_v = float(max_voltage_over_component)
        self.k = float(approx_k_factor)
        self.show_plots = show_plots

        self.validate_inputs()

        # Open device once
        self.the_dev = IBM4_Lib.Ser_Iface()
        self.waveform_plateau_times = {}

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

        self.run_waveform_sweep_increase()
        # self.run_waveform_sweep_decrease()

        self.run_current_cal()

        return dict(self.waveform_plateau_times)


    def close(self) -> None:
        print("Closing IBM4 device connection...")
        """
        Close device connection.
        """
        if hasattr(self, "the_dev") and self.the_dev is not None:
            del self.the_dev
            self.the_dev = None

    # ------------------------------------------------------------------
    # Internal: validation
    # ------------------------------------------------------------------

    def validate_inputs(self) -> None:
        print("Validating inputs...")
        if self.resistor <= 0.0:
            raise ValueError("resistor must be > 0 Ohm")
        if not (0.0 < self.max_v <= 3.3):
            raise ValueError("max_voltage_over_component must be in (0, 3.3] V")
        if self.k <= 0.0:
            raise ValueError("approx_k_factor must be > 0")

    # ------------------------------------------------------------------
    # Internal: waveform sweeps
    # ------------------------------------------------------------------

    def run_waveform_sweep_increase(self) -> None:
        print("Running waveform sweep for current increase...")
        """
        Sweep A0 upwards, measure response times, store in self.waveform_plateau_times.
        """
        A1_voltage = self.max_v
        A0_values = self.max_Voltages(self.resistor, self.k)

        if not A0_values or A0_values[-1] < 0.1:
            raise ValueError("resistor is too large (or approx_k_factor too high); "
                             "max supported A0 is below 0.1 V")

        for A0_voltage in A0_values:
            rt_dict = self._read_waveform_current_increase(
                A0_voltage=A0_voltage,
                A1_voltage=A1_voltage,
                response_times=self.waveform_plateau_times,
            )
            self.waveform_plateau_times.update(rt_dict)


    def run_waveform_sweep_decrease(self) -> None:
        print("Running waveform sweep (decrease)...")
        """
        Sweep A0 downwards, measure response times, store in self.waveform_plateau_times.
        """
        A1_voltage = self.max_v
        A0_values = self.max_Voltages(self.resistor, self.k)

        for A0_voltage in A0_values:
            rt_dict = self._read_waveform_current_decrease(
                A0_voltage=A0_voltage,
                A1_voltage=A1_voltage,
                response_times=self.waveform_plateau_times,
            )
            self.waveform_plateau_times.update(rt_dict)

    # ------------------------------------------------------------------
    # Internal: waveform measurement helpers
    # ------------------------------------------------------------------

    def _read_waveform_current_increase(
        self,
        A0_voltage: float,
        A1_voltage: float,
        response_times: dict | None = None,
        ) -> dict:
        print(f"Measuring increase waveform for A0={A0_voltage} V, A1={A1_voltage} V...")
        """
        Measure current waveform for a given A0 step from zero (increase).
        """
        if response_times is None or not isinstance(response_times, dict):
            response_times = {}

        # Pre-step A1
        self.the_dev.Output_voltage_from_zero(A1_voltage=A1_voltage)
        time.sleep(0.5)

        # Step both A0 and A1
        self.the_dev.Output_voltage_from_zero(A0_voltage=A0_voltage, A1_voltage=A1_voltage)

        Nreads = 5000
        input_ch = "A3"

        start = time.time()
        avg, err, vals = self.the_dev.ReadVoltage(input_ch, "Multiple Voltage", Nreads)
        end = time.time()

        deltaT = end - start
        measurement_time = deltaT / float(Nreads)
        total_time = measurement_time * Nreads
        times = np.linspace(0, total_time, Nreads)

        smooth_waveform = self._smooth_signal(vals, window_size=200)

        _, _, _, response_idx = self._plateau_detection(
            times,
            smooth_waveform,
            segment_length=250,
            A0_voltage=A0_voltage,
            A1_voltage=A1_voltage,
        )

        plateau_time_seconds = (
            times[response_idx]
            if len(times) > response_idx
            else response_idx * measurement_time
        )

        voltage_key = round(float(A0_voltage), 4)
        response_times[voltage_key] = round(float(plateau_time_seconds), 4)

        return response_times

    def _read_waveform_current_decrease(
        self,
        A0_voltage: float,
        A1_voltage: float,
        response_times: dict | None = None,
        ) -> dict:
        print(f"Measuring decrease waveform for A0={A0_voltage} V, A1={A1_voltage} V...")
        """
        Measure current waveform for a given A0 step to zero (decrease).
        """
        if response_times is None or not isinstance(response_times, dict):
            response_times = {}

        # Choose Nreads based on A0
        if A0_voltage < 0.02:
            Nreads = 5000
        elif A0_voltage < 0.03:
            Nreads = 2500
        else:
            Nreads = 1500

        input_ch = "A3"

        # Step down to zero
        self.the_dev.Output_voltage_to_zero(A0_voltage=A0_voltage, A1_voltage=A1_voltage)

        start = time.time()
        avg, err, vals = self.the_dev.ReadVoltage(input_ch, "Multiple Voltage", Nreads)
        end = time.time()

        deltaT = end - start
        measurement_time = deltaT / float(Nreads)
        total_time = measurement_time * Nreads
        times = np.linspace(0, total_time, Nreads)

        smooth_waveform = self._smooth_signal(vals, window_size=200)

        _, _, _, response_idx = self._plateau_detection(
            times,
            smooth_waveform,
            segment_length=250,
            A0_voltage=A0_voltage,
            A1_voltage=A1_voltage,
        )

        plateau_time_seconds = (
            times[response_idx]
            if len(times) > response_idx
            else response_idx * measurement_time
        )

        voltage_key = round(float(A0_voltage), 4)
        response_times[voltage_key] = round(float(plateau_time_seconds), 4)

        return response_times

    # ------------------------------------------------------------------
    # Internal: plateau detection & smoothing
    # ------------------------------------------------------------------

    def _plateau_detection(
        self,
        times,
        values,
        segment_length: int = 250,
        A0_voltage: float = 1.0,
        A1_voltage: float = 1.0,
        ):
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
            plt.title(f"Vin: {A0_voltage} V & A1: {A1_voltage} V")

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

    def _smooth_signal(self, vals, window_size: int):
        print("Smoothing signal with moving average...")
        """
        Apply a moving average twice to smooth the signal.
        """
        kernel = np.ones(window_size) / window_size
        pad_width = window_size // 2

        padded_vals = np.pad(vals, pad_width, mode="edge")
        smoothed_once = np.convolve(padded_vals, kernel, mode="valid")

        padded_once = np.pad(smoothed_once, pad_width, mode="edge")
        smoothed_twice = np.convolve(padded_once, kernel, mode="valid")

        return smoothed_twice[: len(vals)]

    # ------------------------------------------------------------------
    # Internal: max voltage and CurCal
    # ------------------------------------------------------------------

    def max_Voltages(self, resistor: float, approx_k_factor: float):
        print("Computing max supported A0 voltages based on resistor and k-factor...")
        """
        Compute allowed A0 voltages based on resistor and k-factor.
        """
        A0 = [0.01,
              0.02,
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

    def run_current_cal(self) -> None:
        print("Running current calibration sweep...")
        """
        Perform current calibration sweep (CurCal) using plateau times.
        """
        A0_min = 0.0
        A1_voltage = self.max_v

        A0_max_list = self.max_Voltages(self.resistor, self.k)
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
        # for i in range(len(self.waveform_plateau_times)):
        #     self.waveform_plateau_times[i] *= cal_factor[0]

        if sweep_data is None or getattr(sweep_data, "size", 0) == 0:
            raise RuntimeError("SingleChannelSweepC returned no data; calibration sweep failed")

        ch = 3
        sweep_data[:, ch] = sweep_data[:, ch] * 1000.0 / self.resistor  # convert to mA

        cal_factor = np.polyfit(sweep_data[:, 0], sweep_data[:, ch], 1)
        self.waveform_plateau_times["Cal"] = cal_factor[0]
        self.waveform_plateau_times["Cal_intercept"] = cal_factor[1]
        self.waveform_plateau_times["R2"] = np.corrcoef(sweep_data[:, 0], sweep_data[:, ch])[0, 1] ** 2
        self.waveform_plateau_times["resistor"] = self.resistor

        if self.show_plots:
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

        self.waveform_plateau_times["help"] = '"Cal" for calibration factor in mA/V, "Cal_intercept" for intercept in mA, "R2" for R-squared, "resistor" for sense resistor. Current_times lists the A0 voltages used in the waveform sweeps.'  # noqa: E501
    # ------------------------------------------------------------------
    # Internal: save/load to IBM4
    # ------------------------------------------------------------------

    def save_dict_to_IBM4(self, msg_payload=None) -> None:
        print("Saving calibration data to IBM4 firmware...")
        """
        Send a message payload to the IBM4 firmware.
        """
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

    def get_cal(self, key: str | None = None):
        print("Retrieving calibration data from IBM4 firmware...")
        """
        Get saved calibration from IBM4 firmware.
        """
        dev = IBM4_Lib.Ser_Iface()
        try:
            response = dev.Get_Cal_from_IBM4(key=key, loud=False)
            print(response)
            return response
        finally:
            if dev is not None:
                del dev
