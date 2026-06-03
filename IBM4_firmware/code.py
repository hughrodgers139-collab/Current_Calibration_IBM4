import supervisor
import time
import board
import pwmio
import microcontroller
import json
from analogio import AnalogIn
from analogio import AnalogOut

# pwm = pwmio.PWMOut(board.D9, frequency=500)
# pwm = pwmio.PWMOut(board.D9, duty_cycle=2 ** 15, frequency=440, variable_frequency=True)
pwm5 = pwmio.PWMOut(board.D5, duty_cycle=2 ** 15)
pwm7 = pwmio.PWMOut(board.D7, duty_cycle=2 ** 15)
pwm9 = pwmio.PWMOut(board.D9, duty_cycle=2 ** 15)
pwm10 = pwmio.PWMOut(board.D10, duty_cycle=2 ** 15)
pwm11 = pwmio.PWMOut(board.D11, duty_cycle=2 ** 15)
pwm12 = pwmio.PWMOut(board.D12, duty_cycle=2 ** 15)
pwm13 = pwmio.PWMOut(board.D13, duty_cycle=2 ** 15)

# For listening for serial inputs
####
# Define names for In and Out pins
Vout0 = AnalogOut(board.A0)
Vout1 = AnalogOut(board.A1)
Vin2 = AnalogIn(board.A2)
Vin3 = AnalogIn(board.A3)
Vin4 = AnalogIn(board.A4)
Vin5 = AnalogIn(board.A5)
Vin6 = AnalogIn(board.D2) # according to pinout doc pin labelled as 2 is another AI
NRdChLim = 5 # Upper limit for no of channels that can read, previously NRdChLim = 4

B2U_Cal = 14/3

# Define the constants
# For notes on the following see
# https://learn.adafruit.com/circuitpython-basics-analog-inputs-and-outputs/analog-to-digital-converter-inputs
# ADC values in circuit python are all put in the range of 16-bit unsigned values so 0 - 65535 (-1+2**16)
Vmax = Vin2.reference_voltage # max AO/AI value
bit_scale = (-1+(2**16) )#(-1+(64*1024)) # 64 bits

# Functions to convert from 12-bit to Volt.
def dac_value(volts):
    return int(volts / 3.3 * 65535)
    #return int((volts / Vmax)*bit_scale)

def get_voltage(pin):
    return (pin.value * 3.3) / 65535
    #return ((pin.value*Vmax)/bit_scale)

def get_PWM(percentage):
    return (int(percentage/100.0*0xffff+0.5))

def Simple_Vout_A0(command):
    # If the user inputs command a<value> this will be interpreted as setting A0 to the volt level <value>
    try:
        SetVoltage = float(command[1:])
        if SetVoltage >= 0.0 and SetVoltage < Vmax: # Sets limits on the Output voltage to board specs
            Vout0.value = dac_value(SetVoltage) # Set the voltage
        else:
            Vout0.value = dac_value(0.0) # Set the voltage to zero in the event of SetVoltage range error
    except Exception as e:
        print('\nERROR: Simple_Vout_A0\n')
        print(e)

def Simple_Vout_A1(command):
    # If the user inputs command b<value> this will be interpreted as setting A1 to the volt level <value>
    try:
        SetVoltage = float(command[1:])
        if SetVoltage >= 0.0 and SetVoltage < Vmax: # Sets limits on the Output voltage to board specs
            Vout1.value = dac_value(SetVoltage) # Set the voltage
        else:
            Vout1.value = dac_value(0.0) # Set the voltage to zero in the event of SetVoltage range error
    except Exception as e:
        print('\nERROR: Simple_Vout_A1\n')
        print(e)

def Simple_Read():
    try:
        # High-impedance voltage reading Vout = Vin
        V2real = get_voltage(Vin2) # no BP-UP on A2
        V3real = get_voltage(Vin3) # no BP-UP on A3
        V4real = get_voltage(Vin4) # no BP-UP on A4
        V5real = get_voltage(Vin5) # no BP-UP on A5
        # format string to output to nearest 10 mV
        #output_str = '%(v2)0.2f, %(v3)0.2f, %(v4)0.2f, %(v5)0.2f'%{"v2":V2real, "v3":V3real, "v4":V4real, "v5":V5real}
        DC_offset = get_voltage(Vin6) # read the DC offset of the BP-UP circuit
        output_str = '%(v2)0.2f, %(v3)0.2f, %(v4)0.2f, %(v5)0.2f, %(v6)0.2f'%{"v2":V2real, "v3":V3real, "v4":V4real, "v5":V5real, "v6":DC_offset}
        print(output_str) # Prints to serial to be read by LabVIEW
    except Exception as e:
        print('\nERROR: Simple_Read\n')
        print(e)




def Saved_Values(payload):
    # Store message in NVM: bytes 0-1 = length (little-endian), bytes 2+ = UTF-8 data
    try:
        nvm = microcontroller.nvm
        if isinstance(payload, dict):
            # Serialize dictionaries explicitly so they can be reconstructed later.
            msg_txt = json.dumps(payload)
        else:
            msg_txt = str(payload)
        msg = msg_txt.encode('utf-8')
        n = len(msg)
        max_len = len(nvm) - 2
        if n > max_len:
            n = max_len
            msg = msg[:n]
        nvm[0] = n & 0xFF
        nvm[1] = (n >> 8) & 0xFF
        nvm[2:2 + n] = msg
        return True
    except Exception as ex:
        print('ERROR: Save_Message failed')
        print(ex)
        return False


def Load_Dictionary(key=None):
    # Read message from NVM: bytes 0-1 = length (little-endian), bytes 2+ = UTF-8 data
    try:
        nvm = microcontroller.nvm
        n = nvm[0] | (nvm[1] << 8)
        max_len = len(nvm) - 2
        if n == 0 or n > max_len:
            return None
        data = bytes(nvm[2:2 + n])
        decoded = data.decode('utf-8')

        try:
            parsed = json.loads(decoded)
            if key is None:
                if isinstance(parsed, dict):
                    return json.dumps(parsed)
                return str(parsed)
            if isinstance(parsed, dict) and key in parsed:
                return str(parsed[key])
            return None
        except Exception:
            # Backward-compatible fallback for non-JSON payloads.
            if key is None:
                return decoded
            return None
    except Exception as ex:
        print('ERROR: Load_Dictionary failed')
        print(ex)
        return None


while True:
    if supervisor.runtime.serial_bytes_available:   # Listens for a serial command
        command = input()
        
        if command.startswith("*IDN"):
            print('ISBY-UCC-RevA.1')
         #   """
        if command.startswith("Calibrate"):
            try:
                with open("/Calibration.txt", "r") as fp:
                    read_data = fp.read()
                    fp.close()
                    print(str(read_data))
            except OSError as e:  # When the file is not available...
                print('ERROR: Calibration file not available')

            # Split the string at the comma
            numbers = read_data.split(',')

            # Convert the substrings to floats
            K = float(numbers[0])
            KI = float(numbers[1])

        elif command.startswith("Mode"):
            TheMode = int(command[4:])
            print(TheMode)
            
        elif command.startswith("PWM"):
            try:
                Tokens = command[3:].split(":")
                ThePin = int(Tokens[0])
                SetPWM = float(Tokens[1])
                if ThePin == 5:
                    pwm5.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 7:
                    pwm7.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 9:
                    pwm9.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 10:
                    pwm10.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 11:
                    pwm11.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 12:
                    pwm12.duty_cycle = get_PWM(SetPWM)
                elif ThePin == 13:
                    pwm13.duty_cycle = get_PWM(SetPWM)
                else:
                    print('Pin out of range: 5,7,9,10-13')
            except ValueError as ex:
                print('Vset must be an integer')
                print(ex)
            else:
                print("PWMset", ThePin, "=", str(SetPWM), end=' ')
                print()

        elif command.startswith("Write"):
            try:
                Tokens = command[5:].split(":")
                Chan = int(Tokens[0])
                SetVoltage = float(Tokens[1])
                if SetVoltage >= 0 and SetVoltage < 3.31:
                    # Sets limits on the Output voltage to board specs
                    if Chan == 0:
                        Vout0.value = dac_value(SetVoltage)  # Set the voltage
                    elif Chan == 1:
                        Vout1.value = dac_value(SetVoltage)  # Set the voltage
                    else:
                        print('Channel out of range: 0 - 1')
                else:
                    print('Vset out of range: 0 - 3.3V')
            except ValueError as ex:
                print('Vset must be a float')
                print(ex)
            except:
                print('Unknown problem')
            else:
                print("Vset", Chan, "=", str(SetVoltage), end=' ')
                print()

        elif command.startswith("Read"):
            try:
                Tokens = command[4:].split(":")
                Chan = int(Tokens[0])
                N = int(Tokens[1])
                if Chan == 0:
                    Pin = Vin2
                elif Chan == 1:
                    Pin = Vin3
                elif Chan == 2:
                    Pin = Vin4
                elif Chan == 3:
                    Pin = Vin5
                elif Chan == 4:
                    Pin = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if Chan in range(0, NRdChLim) and N > 0:
                    Ref = 0.0
                    Mult = 1
                    if TheMode == 1:
                        for i in range(100):
                            Ref += get_voltage(Vin6)
                        Ref /= 100
                        Mult = B2U_Cal
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = get_voltage(Pin)
                    print("Output", Chan, "=", str((Values[0]-Ref)*Mult), end=' ')
                    for i in range(1, N):
                        print(",", str((Values[i]-Ref)*Mult), end=' ')
                    print()

        elif command.startswith("Average"):
            try:
                Tokens = command[7:].split(":")
                Chan = int(Tokens[0])
                N = int(Tokens[1])
                if Chan == 0:
                    Pin = Vin2
                elif Chan == 1:
                    Pin = Vin3
                elif Chan == 2:
                    Pin = Vin4
                elif Chan == 3:
                    Pin = Vin5
                elif Chan == 4:
                    Pin = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                if N < 1:
                    print('Must average at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if Chan in range(0, NRdChLim) and N > 0:
                    Ref = 0.0
                    Mult = 1
                    if TheMode == 1:
                        for i in range(100):
                            Ref += get_voltage(Vin6)
                        Ref /= 100
                        Mult = B2U_Cal
                    Value = 0.0
                    for i in range(N):
                        Value += get_voltage(Pin)
                    Value /= N
                    print("Average", Chan, "=", str((Value-Ref)*Mult))

        elif command.startswith("BRead"):
            try:
                Tokens = command[5:].split(":")
                Chan = int(Tokens[0])
                N = int(Tokens[1])
                if Chan == 0:
                    Pin = Vin2
                elif Chan == 1:
                    Pin = Vin3
                elif Chan == 2:
                    Pin = Vin4
                elif Chan == 3:
                    Pin = Vin5
                elif Chan == 4:
                    Pin = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if Chan in range(0, NRdChLim) and N > 0:
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = Pin.value
                    print("Output", Chan, "=", str(Values[0]), end=' ')
                    for i in range(1, N):
                        print(",", str(Values[i]), end=' ')
                    print()

        elif command.startswith("Diff_Read"):
            try:
                Tokens = command[9:].split(":")
                ChanPlus = int(Tokens[0])
                if ChanPlus == 0:
                    Pplus = Vin2
                elif ChanPlus == 1:
                    Pplus = Vin3
                elif ChanPlus == 2:
                    Pplus = Vin4
                elif ChanPlus == 3:
                    Pplus = Vin5
                elif ChanPlus == 4:
                    Pplus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                ChanMinus = int(Tokens[1])
                if ChanMinus == 0:
                    Pminus = Vin2
                elif ChanMinus == 1:
                    Pminus = Vin3
                elif ChanMinus == 2:
                    Pminus = Vin4
                elif ChanMinus == 3:
                    Pminus = Vin5
                elif ChanMinus == 4:
                    Pminus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                N = int(Tokens[2])
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if ChanPlus in range(0, NRdChLim) and ChanMinus in range(0, NRdChLim) and N > 0:
                    Mult = 1
                    if TheMode == 1:
                        Mult = B2U_Cal
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = get_voltage(Pplus)-get_voltage(Pminus)
                    print("Output =", str(Values[0]*Mult), end=' ')
                    for i in range(1, N):
                        print(",", str(Values[i]*Mult), end=' ')
                    print()

        elif command.startswith("Diff_Average"):
            try:
                Tokens = command[12:].split(":")
                ChanPlus = int(Tokens[0])
                if ChanPlus == 0:
                    Pplus = Vin2
                elif ChanPlus == 1:
                    Pplus = Vin3
                elif ChanPlus == 2:
                    Pplus = Vin4
                elif ChanPlus == 3:
                    Pplus = Vin5
                elif ChanPlus == 4:
                    Pplus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                ChanMinus = int(Tokens[1])
                if ChanMinus == 0:
                    Pminus = Vin2
                elif ChanMinus == 1:
                    Pminus = Vin3
                elif ChanMinus == 2:
                    Pminus = Vin4
                elif ChanMinus == 3:
                    Pminus = Vin5
                elif ChanMinus == 4:
                    Pminus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                N = int(Tokens[2])
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if ChanPlus in range(0, NRdChLim) and ChanMinus in range(0, NRdChLim) and N > 0:
                    Mult = 1
                    if TheMode == 1:
                        Mult = B2U_Cal
                    Value = 0.0
                    for i in range(N):
                        Value += (get_voltage(Pplus) - get_voltage(Pminus))
                    Value /= N
                    print("Average =", str(Value*Mult))

        elif command.startswith("Diff_BRead"):
            try:
                Tokens = command[10:].split(":")
                ChanPlus = int(Tokens[0])
                if ChanPlus == 0:
                    Pplus = Vin2
                elif ChanPlus == 1:
                    Pplus = Vin3
                elif ChanPlus == 2:
                    Pplus = Vin4
                elif ChanPlus == 3:
                    Pplus = Vin5
                elif ChanPlus == 4:
                    Pplus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                ChanMinus = int(Tokens[1])
                if ChanMinus == 0:
                    Pminus = Vin2
                elif ChanMinus == 1:
                    Pminus = Vin3
                elif ChanMinus == 2:
                    Pminus = Vin4
                elif ChanMinus == 3:
                    Pminus = Vin5
                elif ChanMinus == 4:
                    Pminus = Vin6
                else:
                    print('Channel out of range: 0 - 4')
                N = int(Tokens[2])
                if N < 1:
                    print('Must read at least one value')
            except ValueError as ex:
                print('Channel must be an integer')
                print(ex)
            except:
                print('Unknown problem')
            else:
                if ChanPlus in range(0, NRdChLim) and ChanMinus in range(0, NRdChLim) and N > 0:
                    Values = [0] * N
                    for i in range(N):
                        Values[i] = Pplus.value - Pminus.value
                    print("Output =", str(Values[0]), end=' ')
                    for i in range(1, N):
                        print(",", str(Values[i]), end=' ')
                    print()
        
        elif command.startswith("a"):
            Simple_Vout_A0(command)
        elif command.startswith("b"):
            Simple_Vout_A1(command)
        elif command.startswith("l"):
            Simple_Read()
        # """


        elif command.startswith("Message"):
            try:
                payload = command[len("Message"):].strip()
                if payload:
                    payload_to_save = payload
                    # If payload looks like a JSON object, parse it so Save_Message
                    # receives a dictionary rather than a plain string.
                    if payload.startswith("{") and payload.endswith("}"):
                        try:
                            parsed = json.loads(payload)
                            if isinstance(parsed, dict):
                                payload_to_save = parsed
                        except Exception:
                            payload_to_save = payload

                    ok = Saved_Values(payload_to_save)
                    if ok:
                        print('Message saved: ' + payload)
                    else:
                        print('ERROR: Could not save message')
                else:
                    saved = Load_Dictionary()
                    if saved is None:
                        print('No saved message')
                    else:
                        print('Saved message: ' + saved)

            except Exception as ex:
                print('Unknown problem, Message command not received')
                print(ex)


        elif command.startswith("echo"):
            try:
                # Echo the saved payload, or a specific key if one is provided.
                key = command[len("echo"):].strip()
                payload = Load_Dictionary(key) if key else Load_Dictionary()
                if payload is None:
                    if key:
                        print('No saved value for key: ' + key)
                    else:
                        print('No saved message')
                else:
                    if key:
                        print('Saved value: ' + payload)
                    else:
                        print('Saved message: ' + payload)
            except Exception as ex:
                print('Unknown problem, echo command not received')
                print(ex)

        else:
            print('\nERROR: Unknown command entered\n')



    else:
        pass