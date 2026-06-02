
def CurCal():
    """
    Perform a current calibration
    """
    
    FUNC_NAME = ".CurCal()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    
    for DELAY in [0.1]:
        try:
            # instantiate an object that interfaces with the IBM4
            the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
            approx_k_factor = 80
            # instantiate an object to keep track of the sweep space parameters
            v_start = 1
            v_fixed = 3.3
            resistance = 50.0
            v_end = 2 
            # no_steps = int(abs(v_start - v_end)/0.01)
            no_steps = 10
            print(no_steps)
            
            the_interval = Sweep_Interval.SweepSpace(no_steps, v_start, v_end)

            sweep_data = the_dev.SingleChannelSweepB('A0', the_interval, v_fixed = v_fixed, DELAY = DELAY) # use channel A0 to sweep over the voltage interval
            
            chanel = 3
            sweep_data[:,chanel] = sweep_data[:,chanel]/resistance * 1000
            LOBF = numpy.polyfit(sweep_data[:,0]*1000, sweep_data[:,chanel], 1)
            print("LOBF: ", LOBF)
            plt.plot(sweep_data[:,0]*1000, sweep_data[:,chanel], 'o-')
            plt.plot(sweep_data[:,0]*1000, LOBF[0]*sweep_data[:,0]*1000 + LOBF[1], 'r--', label = 'LOBF + {:0.2f} mA/V'.format(LOBF[0]*1000))
            plt.xlabel("Voltage (mV)")
            plt.ylabel("Current (mA)")
            plt.legend()
            plt.title("Current Calibration")
            plt.text(0.5, 0.9, "delay set to {:0.1f} s, resistance = 50 Ohm".format(DELAY), transform=plt.gca().transAxes, ha='center')
            plt.show()

            # print('Measured data')
            # print(sweep_data)
        

            del the_dev # destructor for the IBM4 object, closes comms
        except Exception as e:
            print(ERR_STATEMENT)
            print(e)


def derivative(vals, times):
    """
    Compute the numerical derivative of vals with respect to times.
    """
    dt = numpy.diff(times)
    dv = numpy.diff(vals)
    return dv / dt

def smooth_signal(vals, window_size):
    """
    Apply a moving average twice to smooth the signal.
    """
    kernel = numpy.ones(window_size) / window_size
    pad_width = window_size // 2
    # Pad with edge values to avoid zeros at the edges
    padded_vals = numpy.pad(vals, pad_width, mode='edge')
    smoothed_once = numpy.convolve(padded_vals, kernel, mode='valid')
    padded_once = numpy.pad(smoothed_once, pad_width, mode='edge')
    smoothed_twice = numpy.convolve(padded_once, kernel, mode='valid')
    # Ensure output length matches input
    return smoothed_twice[:len(vals)]

def Read_Waveform_current(A0_voltage, A1_voltage, Responce_times = None):
    """
    Perform multiple readings to read a waveform
    use the overloaded ReadVoltage Method to obtain an averaged reading
    or use the ReadMultipleVoltage Method directly
    """

    FUNC_NAME = ".Read_Waveform_current()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    
    try:
        # ---------------------------------------------------------------------------------------------------------------------
        the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4 this can be changed in the IBM4 firmware
        # ---------------------------------------------------------------------------------------------------------------------
        the_dev.output_voltage_zero_to_hero(A0_voltage = A0_voltage, A1_voltage = A1_voltage)
        # ---------------------------------------------------------------------------------------------------------------------
        Nreads = 5000 # number of reads
        # ---------------------------------------------------------------------------------------------------------------------
        input_ch = 'A3'
        # Only apply scaling if A0_voltage is not zero or too small

        
        start = time.time()
        avg, err, vals = the_dev.ReadVoltage(input_ch, 'Multiple Voltage', Nreads)
        end = time.time()
        deltaT = end - start


        measurement_time = deltaT / float(Nreads)
        time_for_measurement = measurement_time * Nreads


        times = numpy.linspace(0, time_for_measurement, Nreads)

        double_ma_vals = smooth_signal(vals, window_size = 200)

        plateau_results, near_zero_slopes, slope_values, responce_time, Responce_times = segment_regressions(times, 
                                                                                            double_ma_vals, 
                                                                                            segment_length=250, 
                                                                                            A0_voltage=A0_voltage, 
                                                                                            A1_voltage=A1_voltage, 
                                                                                            Responce_times = Responce_times
                                                                                            )
        
        """        
        plt.axvline(x=responce_time*measurement_time, color='g', linestyle='--', label=f"Response Time: {responce_time:.2f} s")
        plt.show()
        time.sleep(1)
        plt.close()
        """

        Responce_times.append(responce_time*measurement_time)
        print("\n\n")
        print("Response times: ", Responce_times)
        print("\n\n")

        # ---------------------------------------------------------------------------------------------------------------------        
        del the_dev
        # ---------------------------------------------------------------------------------------------------------------------
        return times, double_ma_vals, Responce_times
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def segment_regressions(times, values, segment_length=250, A0_voltage=1, A1_voltage=1, Responce_times = None):
    """
    plt.figure(figsize=(10, 15))
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title(f"current: {A0_voltage*87} mA & A1: {A1_voltage/50*1000} mA")
    """

    t = numpy.asarray(times)
    y = numpy.asarray(values)

    n = len(y)
    results = []
    near_zero_slopes = []
    slope_threshold = 1e-4  
    count = 0
    slope_values = []
    Tolarance = 0.01



    for start in range(0, n, segment_length):
        end = min(start + segment_length, n)
        t_seg = t[start:end]
        y_seg = y[start:end]

        if len(t_seg) < 2:
            continue

        # Means
        t_mean = t_seg.mean()
        y_mean = y_seg.mean()

        # Covariance and variance
        cov = numpy.sum((t_seg - t_mean) * (y_seg - y_mean))
        var = numpy.sum((t_seg - t_mean)**2)
        # -------------------------------------------------treat this later---------------------------------------------------------------------
        if var == 0:
            slope = 0
            intercept = y_mean
            r2 = 0
        else:
            slope = cov / var
            intercept = y_mean - slope * t_mean

            # Predictions
            y_pred = slope * t_seg + intercept

            # R²
            ss_res = numpy.sum((y_seg - y_pred)**2)
            ss_tot = numpy.sum((y_seg - y_mean)**2)
            r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
        # ------------------------------------------------------------------------------------------------------------------------

        results.append({
            "segment_start": start,
            "segment_end": end - 1,
            "slope": slope,
            "intercept": intercept,
            "r2": r2
        })

        if abs(slope) < slope_threshold:
            near_zero_slopes.append({
                "segment_start": start,
                "segment_end": end - 1,
                "slope": slope,
                "intercept": intercept,
                "r2": r2
            })


        """
        if count <5 or A0_voltage < 0.03:
            plt.plot(t_seg, y_seg, 'o')
            plt.plot(t_seg, y_pred, 'r--')
            plt.xlabel("Time (s)", fontsize=14)
            plt.ylabel("Voltage (V)", fontsize=14)
            plt.text(t_seg.mean(), y_seg.mean(), f"s:{slope/A0_voltage:.3f}", fontsize=16)
        """
        count += 1
        slope_values.append(slope/A0_voltage)


    max_slope_segment = max(range(len(slope_values)), key=lambda i: slope_values[i])
    Slope_P1 = max_slope_segment + 1
    Slope_P2 = max_slope_segment + 2
    Slope_P3 = max_slope_segment + 3
    
    Slope_P1_volt_val = results[Slope_P1]
    Slope_P2_volt_val = results[Slope_P2]
    Slope_P3_volt_val = results[Slope_P3]

    Stable_point = y[Slope_P3_volt_val["segment_end"]]


    # Build list of candidate indices in order
    candidates = [
        Slope_P1_volt_val["segment_start"],
        Slope_P1_volt_val["segment_start"] + int(0.5 * segment_length),
        Slope_P1_volt_val["segment_end"],
        Slope_P2_volt_val["segment_start"],
        Slope_P2_volt_val["segment_start"] + int(0.5 * segment_length),
        Slope_P2_volt_val["segment_end"],
        Slope_P3_volt_val["segment_start"],
        Slope_P3_volt_val["segment_start"] + int(0.5 * segment_length),
        Slope_P3_volt_val["segment_end"]
    ]

    i = 0
    responce_time = None

    while i < len(candidates):
        idx = candidates[i]
        if abs(y[idx] - Stable_point) / Stable_point < Tolarance:
            responce_time = idx
            break
        i += 1

    # If none matched, default to last candidate
    if responce_time is None:
        responce_time = Slope_P3_volt_val["segment_end"]


    return results, near_zero_slopes, slope_values, responce_time, Responce_times

    





A0 = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
A1 = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.3]
A1 = [0.5]

resistor = 50.0 # Ohm
Responce_times = []
for A1_voltage in A1:
    for A0_voltage in A0:
        if A1_voltage * 1000.0 / resistor > A0_voltage *87.1: 
            Read_Waveform_current(A0_voltage = A0_voltage, A1_voltage = A1_voltage, Responce_times = Responce_times)
            
            
        
    


plt.plot([a * 87 for a in A0], Responce_times, 'o-')
plt.xlabel("Current (mA)")
plt.ylabel("Response Time (s)")
plt.title("Response Time vs Current")
plt.show()
