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
import os
import numpy
import Sweep_Interval
import IBM4_Lib

import matplotlib

# Avoid Qt Wayland window-activation warnings on Linux Wayland sessions.
if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
    try:
        matplotlib.use("TkAgg")
    except Exception:
        matplotlib.use("Agg")

import matplotlib.pyplot as plt

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
        return None, None
        return None, None

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
        return None, None

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


# Trouble shooting and debugging methods
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


# Calibrate Current source for IBM4

def calibrate(resistor = None, max_voltage_over_commponent = 3.25, show_plots = False, approx_k_factor = 90):
    """
    Current Calibration or CurCal Sweeps throught different currents waveforms
    starting with 0 then jumping to a current output and measureing how long it takes to plateau 
    assuming that is when it has reached the desired current level.
    Check Read_Waveform_current for more details on how the waveform is read and processed to determine the responce time.
    Check Segment_regressions for more details on how the plateau time is determined.
    H.Rodgers 4 - 6 - 2026
    """

    FUNC_NAME = ".CurCal()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME

    the_dev = None  # possibly unnecessary________________________________
    try:
        if resistor is None:
            resistor = 50.0
            print("\nNo resistor value provided, using default of 50 Ohm\n")
        resistor = float(resistor)
        if resistor <= 0.0:
            raise ValueError("resistor must be > 0 Ohm")

        if max_voltage_over_commponent is None:
            max_voltage_over_commponent = 3.25
            print("\nNo max_voltage_over_commponent value provided, using default of 3.25 V\n")
        max_voltage_over_commponent = float(max_voltage_over_commponent)

        if max_voltage_over_commponent <= 0.0 or max_voltage_over_commponent > 3.3:
            raise ValueError("max_voltage_over_commponent must be in the range (0, 3.3] V")

        if approx_k_factor is None:
            approx_k_factor = 90.0
            print("\nNo approx_k_factor value provided, using default of 90, using over estimate to insure no plateau in cal\n")
        approx_k_factor = float(approx_k_factor)
        
        if approx_k_factor <= 0.0:
            raise ValueError("approx_k_factor must be > 0")

        the_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC') # find the first connected IBM4 this can be changed in the IBM4 firmware
                                                 # DC may be unnecessary________________________________
        A1_voltage = max_voltage_over_commponent

        # Note: for A0 = 0.01, there does not apear to be a plateau, 
        # the current is just too small, for A0 = 0.02, there is a very short plateau, for A0 = 0.03 and above, there are clear plateaus that can be used to determine the responce time
        A0 = [0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5] # voltage values to be applied to A0 for the current calibration sweep
        A0 = [v for v in A0 if v <= A1_voltage * resistor  / (approx_k_factor-10)] # filter out values that are above the voltage limit over the component

        # Collect response times keyed by input voltage._______________________________

        IBM4_Dict = {}      # dictinary to save 
        max_supported_a0 = A1_voltage * resistor  / (approx_k_factor-10)

        if max_supported_a0 < 0.075: # this is a bit of an arbitrary threshold, but it is based on the observation that for A0 = 0.01, there does not apear to be a plateau, for A0 = 0.02, there is a very short plateau, for A0 = 0.03 and above, there are clear plateaus that can be used to determine the responce time
            raise ValueError(
                "resistor is too large (or approx_k_factor too high) for this voltage limit; "
                "max supported A0 is below 0.075 V"
            )

        for A0_voltage in A0:

            # check if the current is within the range of voltage limit over the resistor
            if A1_voltage * 1000.0 / resistor / approx_k_factor > A0_voltage: 

                IBM4_Dict = Read_Waveform_current( # Function that measures the time for the current to plateau and saves it to a dictionary with Vin A0 as the keys
                    A0_voltage=A0_voltage,
                    A1_voltage=A1_voltage,
                    Responce_times=IBM4_Dict,
                    show_plots=show_plots,
                    the_dev=the_dev
                )
            # Return Nan for values that are out of range of the voltage limit over the resistor 
            else:
                voltage_key = round(float(A0_voltage), 4)
                IBM4_Dict[voltage_key] = numpy.nan

        # CurCal is designed to Find the calibration factor taking into account the time taken to get to get to the current levels
        CurCal(Waveform_plataue_times = IBM4_Dict, show_plots=show_plots, resistor=resistor, approx_k_factor=approx_k_factor)
        # Reuse the same open connection to save results.
        print(IBM4_Dict)
    
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
        return None
    
    # close communications with the IBM4, if it was open
    finally:
        if the_dev is not None:
            del the_dev

def Read_Waveform_current(A0_voltage, A1_voltage, Responce_times=None, show_plots=False, the_dev=None):
    """
    Read the current waveform for a given A0 voltage starting from zero to measure its responce time
    H.Rodgers 4 - 6 - 2026
    """

    FUNC_NAME = ".Read_Waveform_current()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    
    local_dev = None # i may need to go back and fix all of these the_dev

    try:
        if Responce_times is None:
            Responce_times = {}
        elif not isinstance(Responce_times, dict):
            Responce_times = {}

        if the_dev is None:
            local_dev = IBM4_Lib.Ser_Iface(read_mode = 'DC')
            the_dev = local_dev

        # these are values that i have foudn to be more than sufficient to capture the waveform for that voltage,
        # just makes it go a little faster
        if A0_voltage < 0.01:
            Nreads = 8000 # number of reads
        elif A0_voltage < 0.02:
            Nreads = 5000 # number of reads
        elif A0_voltage < 0.03:
            Nreads = 2500 # number of reads
        else:
            Nreads = 1500 # number of reads
        
        input_ch = 'A3'
        # sets voltage to zero, waits a moment, then sets both voltages
        the_dev.Output_voltage_from_zero(A0_voltage = A0_voltage, A1_voltage = A1_voltage)

        # measures time to for waveform  
        start = time.time()
        # waveform voltage measurements
        avg, err, vals = the_dev.ReadVoltage(input_ch, 'Multiple Voltage', Nreads)
        end = time.time()
        deltaT = end - start
        measurement_time = deltaT / float(Nreads)
        time_for_measurement = measurement_time * Nreads
        times = numpy.linspace(0, time_for_measurement, Nreads)

        smooth_wave_form = smooth_signal(vals, window_size = 200)

        _, _, _, responce_time = Plateau_detection(times,
                                                   smooth_wave_form,
                                                   segment_length=250,
                                                   A0_voltage=A0_voltage,
                                                   A1_voltage=A1_voltage,
                                                   show_plots=show_plots
                                                   )
        
        if show_plots: 
            plt.axvline(x=responce_time*measurement_time, color='g', linestyle='--', label=f"Response Time: {responce_time:.4f} s")
            plt.show()        

        plateau_time_seconds = times[responce_time] if len(times) > responce_time else responce_time * measurement_time
        voltage_key = float(f"{A0_voltage:.4f}"[:-1])
        Responce_times[voltage_key] = round(float(plateau_time_seconds), 4)

        return Responce_times
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
        return Responce_times
    finally:
        if local_dev is not None:
            del local_dev

def Plateau_detection(times, values, segment_length=250, A0_voltage=1, A1_voltage=1, show_plots=False):
    """
    Detect the plateau in the waveform by performing linear regression on segments of the data and finding where the slope
    becomes sufficiently small.
    H.Rodgers 4 - 6 - 2026
    """

    FUNC_NAME = ".Plateau_detection()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    results = []
    slope_values = []
    candidates = []
    responce_time = 0
    try:
        if show_plots:
            plt.figure(figsize=(10, 15))
            plt.xlabel("Time (s)")
            plt.ylabel("Voltage (V)")
            plt.title(f"Vin: {A0_voltage} V & A1: {A1_voltage} V")
    

        t = numpy.asarray(times)
        y = numpy.asarray(values)
        n = len(t)

        if n == 0 or len(y) == 0:
            return results, slope_values, candidates, responce_time

        Tolarance = 0.01

        for start in range(0, n, segment_length):
            end = min(start + segment_length, n)
            t_seg = t[start:end]
            y_seg = y[start:end]

            if len(t_seg) <= 4:
                continue

            # Means
            t_mean = t_seg.mean()
            y_mean = y_seg.mean()

            # Covariance and variance
            cov = numpy.sum((t_seg - t_mean) * (y_seg - y_mean))
            var = numpy.sum((t_seg - t_mean)**2)

            if var == 0:
                slope = 0
                intercept = y_mean
                r2 = 0
                y_pred = numpy.full_like(t_seg, fill_value=y_mean, dtype=float)
            else:
                slope = cov / var
                intercept = y_mean - slope * t_mean

                # Predictions
                y_pred = slope * t_seg + intercept

                # R²
                ss_res = numpy.sum((y_seg - y_pred)**2)
                ss_tot = numpy.sum((y_seg - y_mean)**2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            results.append({
                "segment_start": start,
                "segment_end": end - 1,
                "slope": slope,
                "intercept": intercept,
                "r2": r2
            })

            if show_plots:
                plt.plot(t_seg, y_seg, 'o')
                plt.plot(t_seg, y_pred, 'r--')
                plt.xlabel("Time (s)", fontsize=14)
                plt.ylabel("Voltage (V)", fontsize=14)
                if abs(A0_voltage) > 1e-12:
                    slope_norm = slope / A0_voltage
                else:
                    slope_norm = slope
                plt.text(t_seg.mean(), y_seg.mean(), f"s:{slope_norm:.4f}", fontsize=16)
                
            if abs(A0_voltage) > 1e-12:
                slope_values.append(slope / A0_voltage)
            else:
                slope_values.append(slope)

        if len(results) == 0 or len(slope_values) == 0:
            return results, slope_values, candidates, responce_time

        max_slope_segment = max(range(len(slope_values)), key=lambda i: slope_values[i])
        Slope_P1 = min(max_slope_segment + 1, len(results) - 1)
        Slope_P2 = min(max_slope_segment + 2, len(results) - 1)
        Slope_P3 = min(max_slope_segment + 3, len(results) - 1)
        
        Slope_P1_volt_val = results[Slope_P1]
        Slope_P2_volt_val = results[Slope_P2]
        Slope_P3_volt_val = results[Slope_P3]

        Stable_point = y[Slope_P3_volt_val["segment_end"]]


        # Build list of candidate indices in order
        candidates = [
            Slope_P1_volt_val["segment_start"],
            Slope_P1_volt_val["segment_start"] + int(0.25 * segment_length),
            Slope_P1_volt_val["segment_start"] + int(0.5 * segment_length),
            Slope_P1_volt_val["segment_start"] + int(0.75 * segment_length),
            Slope_P1_volt_val["segment_end"],
            Slope_P2_volt_val["segment_start"],
            Slope_P2_volt_val["segment_start"] + int(0.25 * segment_length),
            Slope_P2_volt_val["segment_start"] + int(0.5 * segment_length),
            Slope_P2_volt_val["segment_start"] + int(0.75 * segment_length),
            Slope_P2_volt_val["segment_end"],
            Slope_P3_volt_val["segment_start"],
            Slope_P3_volt_val["segment_start"] + int(0.25 * segment_length),
            Slope_P3_volt_val["segment_start"] + int(0.5 * segment_length),
            Slope_P3_volt_val["segment_start"] + int(0.75 * segment_length),
            Slope_P3_volt_val["segment_end"]
        ]

        i = 0
        responce_time = None

        while i < len(candidates):
            idx = candidates[i]
            idx = min(max(0, idx), len(y) - 1)
            if Stable_point == 0:
                close_enough = abs(y[idx] - Stable_point) < Tolarance
            else:
                close_enough = abs(y[idx] - Stable_point) / abs(Stable_point) < Tolarance

            if close_enough:
                responce_time = idx
                break
            i += 1

        # If none matched, default to last candidate
        if responce_time is None:
            responce_time = Slope_P4_volt_val["segment_end"]
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)

    return results, slope_values, candidates, responce_time

def smooth_signal(vals, window_size):
    """
    Apply a moving average twice to smooth the signal.
    """
    FUNC_NAME = ".smooth_signal()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    try:
        kernel = numpy.ones(window_size) / window_size
        pad_width = window_size // 2
        # Pad with edge values to avoid zeros at the edges
        padded_vals = numpy.pad(vals, pad_width, mode='edge')
        smoothed_once = numpy.convolve(padded_vals, kernel, mode='valid')
        padded_once = numpy.pad(smoothed_once, pad_width, mode='edge')
        smoothed_twice = numpy.convolve(padded_once, kernel, mode='valid')
        # Ensure output length matches input
        return smoothed_twice[:len(vals)]
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
        return vals

def CurCal(Waveform_plataue_times = None, show_plots = False, resistor = None, approx_k_factor = None):
    """
    Perform a current calibration by sweeping through different current levels and measuring the time taken 
    to reach the plateau for each level.
    H.Rodgers 4 - 6 - 2026
    """
    
    FUNC_NAME = ".CurCal()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    
    for DELAY in [0.1]:
        try:
            the_dev = IBM4_Lib.Ser_Iface() # may have to take out_____________________________
            if Waveform_plataue_times is None or not isinstance(Waveform_plataue_times, dict):
                Waveform_plataue_times = {}
            if approx_k_factor is None:
                approx_k_factor = 90
            approx_k_factor = float(approx_k_factor)
            if approx_k_factor <= 0.0:
                raise ValueError("approx_k_factor must be > 0")
            # instantiate an object to keep track of the sweep space parameters
            A0_min = 0.0
            A1_voltage = 3.3
            if resistor is None:
                resistor = 50.0
            resistor = float(resistor)
            if resistor <= 0.0:
                raise ValueError("resistor must be > 0 Ohm")
            3.25 * 10 / 80
            A0_max = A1_voltage * resistor  / (approx_k_factor-10) # convert to volts
            if A0_max < 0.01:
                raise ValueError("resistor is too large for requested calibration range")
            no_steps = int(A0_max / 0.01)
            print(A0_max, no_steps)
            no_steps = max(no_steps, 2)
            print("\n",A0_max, A1_voltage, resistor, approx_k_factor, no_steps, "\n")



            the_interval = Sweep_Interval.SweepSpace(no_steps, A0_min, A0_max)

            sweep_data = the_dev.SingleChannelSweepC('A0', the_interval, v_fixed = A1_voltage, resistor = resistor, waveform_plataue_times = Waveform_plataue_times) # use channel A0 to sweep over the voltage interval
            
            chanel = 3
            sweep_data[:,chanel] = sweep_data[:,chanel] *1000.0 / resistor # convert to mA
            Cal_factor = numpy.polyfit(sweep_data[:,0], sweep_data[:,chanel], 1)
            Waveform_plataue_times['Cal'] = Cal_factor[0]
            Waveform_plataue_times['Cal_intercept'] = Cal_factor[1]
            Waveform_plataue_times['R2'] = numpy.corrcoef(sweep_data[:,0], sweep_data[:,chanel])[0,1]**2

            if show_plots == False:
                print("Cal_factor: ", Cal_factor)
                plt.plot(sweep_data[:,0], sweep_data[:,chanel], 'o-')
                plt.plot(sweep_data[:,0], Cal_factor[0]*sweep_data[:,0] + Cal_factor[1], 'r--', label = 'Cal_factor + {:0.2f} mA/V'.format(Cal_factor[0]))
                plt.xlabel("Voltage (mV)")
                plt.ylabel("Current (mA)")
                plt.legend()
                plt.title("Current Calibration")
                plt.text(0.5, 0.9, "delay set to {:0.1f} s, resistor = {:0.1f} Ohm".format(DELAY, resistor), transform=plt.gca().transAxes, ha='center')
                plt.show()


            Waveform_plataue_times["help"] = "\"cal\" for calibration factor in mA/V and \"Cal\" for the intercept in mA, \"R2\" for the R-squared value of the fit,"
            payload = dict(sorted(Waveform_plataue_times.items(), key=lambda kv: (isinstance(kv[0], str), str(kv[0]))))

            Save_dict_to_IBM4(payload, the_dev=the_dev)
                              
        

            del the_dev # destructor for the IBM4 object, closes comms
        except Exception as e:
            print(ERR_STATEMENT)
            print(e)


# IBM4 save and send data

def Save_dict_to_IBM4(msg_payload=None, the_dev=None):
    """
    Send a message payload to the IBM4 firmware.

    Inputs:
    msg_payload (type: dict | str | None)
    If None, a default dictionary payload is sent.
    """
    
    FUNC_NAME = ".Save_dict_to_IBM4()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    
    local_dev = None

    try:
        # instantiate an object that interfaces with the IBM4
        if the_dev is None:
            local_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default
            the_dev = local_dev
        response = the_dev.send_mes(msg=msg_payload)
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
    finally:
        if local_dev is not None:
            del local_dev # destructor for the IBM4 object, closes comms

def Get_cal(Key=None):
    """
    Echo the saved data from the IBM4 display.

    Inputs:
    Key (type: str | None) optional dictionary key to query.

    Returns:
    str | None: saved payload text/value if present, else None
    """
    
    FUNC_NAME = ".Get_cal()"
    ERR_STATEMENT = "Error: " + MOD_NAME_STR + FUNC_NAME
    
    try:
        # instantiate an object that interfaces with the IBM4
        the_dev = IBM4_Lib.Ser_Iface() # find the first connected IBM4, open in DC mode by default

        response = the_dev.Get_Cal_from_IBM4(key=Key, loud=False)
        print(response)

       
        del the_dev # destructor for the IBM4 object, closes comms
        return response
    except Exception as e:
        print(ERR_STATEMENT)
        print(e)
        return None
