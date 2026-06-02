"""
Methods for testing the operation of the IBM4 Serial Controller Class

0. Basic Find, Open, Close
1. Step through voltages
2. Basic single channel sweep
3. Read all input channels
4. Differential read
5. Multi-reads and timings
6. Multimeter mode
7. Linear single channel sweep

R. Sheehan 12 - 6 - 2024
"""


import time
import numpy
import Sweep_Interval
import IBM4_Lib
import matplotlib.pyplot as plt

# --- Moving average and smoothing utilities (module level) ---

MOD_NAME_STR = "Control_Examples"

def Simple_Open_Close():
    """
    See if an IBM4 is connected to the PC, if so, open it and then close it
    """
    
    FUNC_NAME = ".Simple_Open_Close()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        #the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4, open in DC mode
        
        #the_dev = IBM4_Lib.Ser_Iface(read_mode = 'AC') # find the first connected IBM4, open in AC mode
        
        #the_dev = IBM4_Lib.Ser_Iface('COM3', read_mode='AC') # connect to a named IBM4, open in AC mode

        print("IBM4 IDN string:", the_dev.IdentifyIBM4() )

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Step_Through_Voltages():
    """
    Connect to an IBM4, output voltage from a channel, increase that voltage, make a reading
    """
    
    FUNC_NAME = ".Step_Through_Voltages()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        output_ch = 'A1' # select the voltage output channel either A0 or A1
        input_ch = 'A2' # select the voltage input channel A2, A3, A4, A5, D2

        print("Analog Output Steps + Averaged Read on Single Channel")
        print("Analog Out:",output_ch)
        print("Analog In:",input_ch)   

        volt_val = 1.0
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 1.5
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 2.0
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 1.7
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        volt_val = 0.7
        the_dev.WriteVoltage(output_ch, volt_val)
        time.sleep(2)

        avg_val = the_dev.ReadAverageVoltage(input_ch, no_reads = 10, loud = False)
        print("Set voltage value = ",volt_val)
        print("Recorded average voltage = ",avg_val)

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Simple_Sweep():
    """
    Perform simple sweep and read on a single channel
    """
    
    FUNC_NAME = ".Simple_Sweep()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        output_ch = 'A1' # select the voltage output channel either A0 or A1
        input_ch = 'A2' # select the voltage input channel A2, A3, A4, A5, D2
        Nreads = 51 # no. readings at each channel
        volts = numpy.arange(0, 3.1, 1)

        print("Analog Output Sweep + Averaged Read on Single Channel")
        print("Analog Out:",output_ch)
        print("Analog In:",input_ch)
        
        start = time.time()
        for v in volts:
            the_dev.WriteVoltage(output_ch, v)
            reading = the_dev.ReadAverageVoltage(input_ch, Nreads)
            print('Vset:',v,', Vread: ',reading)
        end = time.time()
        deltaT = end-start
        readsTot = len(volts)*Nreads
        measT = deltaT/(float(readsTot))
        SR = 1.0/measT
        print("%(v1)d measurements performed in %(v2)0.3f seconds => SR = %(v3)0.3f Hz"%{"v1":readsTot, "v2":deltaT, "v3":SR})

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Simple_Sweep_Read_All():
    """
    Perform simple sweep and read on all input channel
    """
    
    FUNC_NAME = ".Simple_Sweep_Read_All()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        output_ch = 'A1' # select the voltage output channel either A0 or A1
        Nreads = 31 # no. readinngs at each channel
        NAI = 5 # no. analog input channels
        volts = numpy.arange(0, 3.1, 0.5)

        print("Analog Output Sweep + Averaged Read on All Channels")
        print("Analog Out:",output_ch)

        start = time.time()
        for v in volts:
            the_dev.WriteVoltage(output_ch, v)
            readings = the_dev.ReadAverageVoltageAllChnnl(Nreads)
            print('Vset:',v,', Vread: ',readings)
        end = time.time()
        deltaT = end-start
        readsTot = len(volts)*Nreads*NAI
        measT = deltaT/(float(readsTot))
        SR = 1.0/measT
        print("%(v1)d measurements performed in %(v2)0.3f seconds => SR = %(v3)0.3f Hz"%{"v1":readsTot, "v2":deltaT, "v3":SR})

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Differential_Readings():
    """
    Perform differential reads between different pairs of channels
    use the overloaded DifferentialRead Method to obtain an averaged reading

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Differential_Readings()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        # this assumes that you are reading the voltage across a resistor and diode in series
        # A2 set to Vin, A3 between the resistor and the diode, A4 at GND
        Nreads = 237
        Rval = 10.0 / 1000.0 # sense resistance in kOhm
        Vset = 2.25
        output_ch = 'A0' # select the voltage output channel either A0 or A1

        print("Differential Reads on Different Analog Inputs")
        print("Analog Out: ",output_ch)
        
        the_dev.WriteVoltage(output_ch, Vset)
        time.sleep(1) # give it some time to settle

        vals = the_dev.DifferentialRead('A2', 'A4', 'Multiple Voltage', Nreads)
        print("Vhi: A2, Vlo: A4")
        print("Set Voltage: %(v1)0.3f +/- %(v2)0.3f (V)"%{"v1":vals[0],"v2":vals[1]})

        vals = the_dev.DifferentialRead('A2', 'A3', 'Multiple Voltage', Nreads)
        print("Vhi: A2, Vlo: A3")
        print("Sense Voltage: %(v1)0.3f +/- %(v2)0.3f (V)"%{"v1":vals[0],"v2":vals[1]})
        print("Sense Current: %(v1)0.1f +/- %(v2)0.1f (mA)"%{"v1":vals[0]/Rval,"v2":vals[1]/Rval})
        
        vals = the_dev.DifferentialRead('A3', 'A4', 'Multiple Voltage', Nreads)
        print("Vhi: A3, Vlo: A4")
        print("Diode Voltage: %(v1)0.3f +/- %(v2)0.3f (V)"%{"v1":vals[0],"v2":vals[1]})
        
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Multiple_Readings():
    """
    Perform multiple readings by different methods
    use the overloaded ReadVoltage Method to obtain an averaged reading

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Multiple_Readings()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        
        # can compare the timing of each of the different measurement types
        # https://stackoverflow.com/questions/7370801/how-do-i-measure-elapsed-time-in-python
        # ReadAverageVoltage is slightly faster than ReadAverageVoltageMultiple
        # which is weird considering that ReadAverageVoltage has to do extra processing on chip
        # Sample Rate for IBM4 is variable, as we know and find annoying
        # Can see that nothing wrong with timing of ReadAverageVoltageAllChnnl
        # Execution of ReadAverageVoltageAllChnnl takes ~ 5 ReadAverageVoltage which makes sense really
        # since ReadAverageVoltageAllChnnl consists of 5 calls to ReadAverageVoltage
        # R. Sheehan 9 - 7 - 2024

        Nreads = 501
        Vset = 1.5
        output_ch = 'A1'
        the_dev.WriteVoltage(output_ch,Vset)
        time.sleep(1)

        print("Multiple Reads by Different Methods - Test the Overloaded ReadVoltage method")
        print("Analog Out:",output_ch)
        print("Vset =",Vset,"(V)\n")

        # time the measurement
        start = time.time()
        #avg, err, vals = the_dev.ReadMultipleVoltage('A3', Nreads)
        avg, err, vals = the_dev.ReadVoltage('A3', 'Multiple Voltage', Nreads)
        end = time.time()
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        print("Analog Input: A3, Read Method: Multiple Voltage => ReadMultipleVoltage")
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR })
        print("Measured Voltage: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg,"v2":err})

        start = time.time()
        #val = the_dev.ReadAverageVoltage('A3',Nreads)
        val = the_dev.ReadVoltage('A3','Average Voltage', Nreads)
        end = time.time()
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        print("Analog Input: A3, Read Method: Average Voltage => ReadAverageVoltage")
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR })
        print("Measured Voltage: %(v1)0.3f (V)\n"%{"v1":val})

        start = time.time()
        val = the_dev.ReadAverageVoltageAllChnnl(Nreads)
        end = time.time()
        deltaT = end-start
        measT = deltaT/(float(Nreads*5))
        SR = 1.0/measT
        print("Analog Input: All, Read Method: ReadAverageVoltageAllChnnl")
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads*5, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR})
        print("Measured Voltages: ", val)
        #print("\nSR from each Read method are comparable")

        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
    
def Read_Waveform():
    """
    Perform multiple readings to read a waveform
    use the overloaded ReadVoltage Method to obtain an averaged reading
    or use the ReadMultipleVoltage Method directly

    the user must be careful when using overloaded methods
    python allows for different return types and different numbers of returned elements
    what is not forbidden is permitted and exploited
    """
    
    FUNC_NAME = ".Read_Waveform()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4
        
        Nreads = 501 # no. readings to be made        
        input_ch = 'A3' # analog input channel on which readings are to be made

        # time the measurement

        start = time.time()

        
        # overloaded call to ReadMultipleVoltage
        avg, err, vals = the_dev.ReadVoltage(input_ch, 'Multiple Voltage', Nreads)
        
        # Direct call to ReadMultipleVoltage
        # avg, err, vals = the_dev.ReadMultipleVoltage(input_ch, Nreads) # 
        
        end = time.time()

        # compute the time taken to perform all the measurements
        # this time does not include the overheads incurred by the IBM4 itself
        deltaT = end-start
        measT = deltaT/(float(Nreads))
        SR = 1.0/measT
        
        print("Analog Input: %(v1)s, Read Method: Multiple Voltage => ReadMultipleVoltage"%{"v1":input_ch})
        print("%(v1)d measurements performed in %(v2)0.3f seconds"%{"v1":Nreads, "v2":deltaT})
        print("%(v1)0.4f secs / measurement"%{"v1":measT})
        print("Sample Rate: %(v1)0.2f Hz"%{"v1":SR})
        print("Measured Average Voltage: %(v1)0.3f +/- %(v2)0.3f (V)\n"%{"v1":avg,"v2":err})

        # Make a plot of the recorded waveform if you desire
        # Write the data to a file, make a plot elsewhere

        
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Multimeter_Mode():
    """
    Run the IBM4 in multimeter mode
    """
    
    FUNC_NAME = ".Multimeter_Mode()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        the_dev.MultimeterMode() # I rock
       
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Linear_Sweep_V1():
    """
    Perform a linear sweep on chosen channels
    """
    
    FUNC_NAME = ".Linear_Sweep_V1()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        # instantiate an object to keep track of the sweep space parameters
        no_steps = 10
        v_start = 0.0
        v_end = 3.3
        v_fixed = 1.0

        # A0 will sweep while A1 will be kept constant at v_fixed
        # I wonder what that could be used for? 
        sweep_data = the_dev.SingleChannelSweepA('A0', v_start, v_end, no_steps, v_fixed) # use channel A0 to sweep over the voltage interval

        print('Measured data')
        print(sweep_data)
       
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def Linear_Sweep_V2():
    """
    Perform a linear sweep on chosen channels
    """
    
    FUNC_NAME = ".Linear_Sweep_V2()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        # instantiate an object to keep track of the sweep space parameters
        no_steps = 10
        v_start = 0.0
        v_end = 3.3
        the_interval = Sweep_Interval.SweepSpace(no_steps, v_start, v_end)

        # A1 will sweep while A0 will be kept constant at v_fixed
        # I wonder what that could be used for? 
        sweep_data = the_dev.SingleChannelSweepB('A1', the_interval, v_fixed = 0.0) # use channel A1 to sweep over the voltage interval

        print('Measured data')
        print(sweep_data)
       
        del the_dev # destructor for the IBM4 object, closes comms
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

def read_all_channels_live(no_reads = 31, refresh_time = 0.2):
    """
    Continuously read all channels and refresh output in-place.

    Stop by pressing Ctrl+C.
    """

    FUNC_NAME = ".read_all_channels_live()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    try:
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
        ch_names = ['A2', 'A3', 'A4', 'A5', 'D2']

        print("Live channel voltages (Ctrl+C to stop):")
        while True:
            vals = the_dev.ReadAverageVoltageAllChnnl(no_reads)
            line = " | ".join(["%(v1)s: %(v2)0.4f V"%{"v1":ch, "v2":val} for ch, val in zip(ch_names, vals)])
            print("\r" + line + "   ", end = "", flush = True)
            time.sleep(refresh_time)
    except KeyboardInterrupt:
        print("\nStopped live reading.")
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
    finally:
        try:
            del the_dev # destructor for the IBM4 object, closes comms
        except Exception:
            pass



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

def Read_Waveform_current(A0_voltage, A1_voltage, Responce_times = []):
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
        
        # """        
        plt.axvline(x=responce_time*measurement_time, color='g', linestyle='--', label=f"Response Time: {responce_time:.2f} s")
        plt.show()
        time.sleep(1)
        plt.close()
        # """

        Responce_times.append(responce_time*measurement_time)
        print("\n\n")
        print("Response times: ", numpy.round(Responce_times, 3))
        print("\n\n")

        # ---------------------------------------------------------------------------------------------------------------------        
        del the_dev
        # ---------------------------------------------------------------------------------------------------------------------
        return times, double_ma_vals, Responce_times
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)



def segment_regressions(times, values, segment_length=250, A0_voltage=1, A1_voltage=1, Responce_times = None):
    # """
    plt.figure(figsize=(10, 15))
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title(f"current: {A0_voltage*87} mA & A1: {A1_voltage/50*1000} mA")
    # """

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


        # """
        if count <5 or A0_voltage < 0.03:
            plt.plot(t_seg, y_seg, 'o')
            plt.plot(t_seg, y_pred, 'r--')
            plt.xlabel("Time (s)", fontsize=14)
            plt.ylabel("Voltage (V)", fontsize=14)
            plt.text(t_seg.mean(), y_seg.mean(), f"s:{slope/A0_voltage:.3f}", fontsize=16)
        # """
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

    



"""

A0 = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.5, 2.0, 2.5, 3.0, 3.3]
A1 = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.3]

resistor = 50.0  # Ohm


# Collect response times for each A1 and A0 combination as a 2D array
Responce_time_all = []
for A1_voltage in A1:
    row = []
    for A0_voltage in A0:
        if A1_voltage * 1000.0 / resistor > A0_voltage * 87.1:
            _, _, responce_times = Read_Waveform_current(
                A0_voltage=A0_voltage,
                A1_voltage=A1_voltage
            )
            # Append only the last response time (scalar)
            row.append(responce_times[-1] if responce_times else numpy.nan)
        else:
            row.append(numpy.nan)
    Responce_time_all.append(row)

Responce_time_all = numpy.array(Responce_time_all)

# Plotting all response times for each A1
for i, A1_voltage in enumerate(A1):
    plt.plot([a0 * 87 for a0 in A0], Responce_time_all[i, :], marker='o', label=f"Voltage limit: {A1_voltage} V")

plt.xlabel("Current (mA)")
plt.ylabel("Response Time (s)")
plt.title("Response Time vs Current for Different Voltage Limits with 1% Tolerance")
plt.legend()
plt.show()
plt.show()


"""