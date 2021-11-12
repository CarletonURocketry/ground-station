# Ground station software for communication with the CU-InSpace rocket via an
# RN2483 LoRa radio module.
# Authors:

import serial as ser

# set constants


def init_ground_station():

    # notes from arsalan: why is there a space after every command (ex. "radio set pwr_"
    # does \r\n also work for ios systems?
    # does the radio always respond when we give it any command? Because then we can put the check_for_ok() function in the write() function

    # initlize a serial port
    ser = serial.Serial(
        timeout=1,
        baudrate=57600,
        # number of bits per bytes ((configure packet size?)
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,  # set parity check: no parity
        stopbits=0,  # number of stop bits
        rtscts=False,  # disable hardware (RTS/CTS) flow control
    )
   # set the frequency of the radio
    radio_set_freq(433050000)
    # set the power to -14 db
    radio_set_pwr(14)
    # set the spreading factor
    radio_set_sf("sf9")
    # set the coding rate
    radio_set_cr("4/7")
    # set bandwdith
    radio_set_bw(500)
    # set prlen preamble length
    radio_set_prlen(6)
    # set crc
    radio_set_crc("on")
    # set iqi
    radio_set_iqi("on")
    # set sync word to be 0x43
    radio_set_sync("43")
    print("sucessfully configured lora radio")


def write_to_ground_station(register: int):
    """writes data to the ground station via UART
       author: tarik, Fahim
       step 1: rudimentary write
       step 2: commands? 
       @param register:address of the register you want to write to"""


def read_from_ground_station(register: int):
    """reads data from the ground station via UART and puts it into the 
       correct data format to be passed onto the UI (check the logging format)
       author: elias 
       @param  register: address of register to read from
       @return data: the data that is stored in that register
    """


def load_map():
    """load in a map that can be used offline
        author: """

# wait for serial response we have set a timeout value so it will wait for a response and checks if it's not ok
def wait_for_ok():
   # flush the serial port
    ser.flush()

    rv = ser.readline()
    if rv == bytes('ok'):  # check for ok and report if param invalid

        return ture
    else:
        return false

# set frequencies based on what possible frequencies can be set to values can be 
# 50000, 125000, 62500.0, 31300.0, 15600.0, 7800.0, 3900.0,
#  200000, 100000, 50000, 25000, 12500.0, 6300.0, 3100.0, 166700.0, 83300.0, 41700.0, 20800.0, 10400.0, 5200.0, 2600.0
def radio_set_freq(freq):
    frequencies = [250000, 125000, 62500.0, 31300.0, 15600.0, 7800.0, 3900.0,
                   200000, 100000, 50000, 25000, 12500.0, 6300.0, 3100.0, 166700.0, 83300.0, 41700.0, 20800.0, 10400.0, 5200.0, 2600.0]
    if freq in frequencies:
        write_to_ground_station(str("radio set pwr "+freq + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error sent to radio")
    print("invalid param")

# set power possible values between -3 and 14 db
def radio_set_pwr(pwr):
    if pwr in range(-3, 14):
        write_to_ground_station(str("radio set pwr "+pwr + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")

# set spreading factor can only be set to  sf7", "sf8", "sf9", "sf10", "sf11", "sf12"]
def radio_set_sf(sf):
    if sf in range["sf7", "sf8", "sf9", "sf10", "sf11", "sf12"]:
        write_to_ground_station(str("radio set sf "+sf + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")

# set coding rate which can only be "4/5", "4/6", "4/7", "4/8"
def radio_set_cr(cr):
    if cr in ["4/5", "4/6", "4/7", "4/8"]:
        write_to_ground_station(str("radio set cr "+cr + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")


# set the bandwidth which can only  be 125 250 or 500 hz
def radio_set_bw(bw):
    if bw in [125, 250, 500]:
        write_to_ground_station(str("radio set bw "+bw + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")


# set IQI to be on or off
def radio_set_iqi(iqi):
    if iqi in ["on", "off"]:
        write_to_ground_station(str("radio set iqi "+iqi + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")

# set sync word it's a 2 bytes 
def radio_set_sync(sync):
    write_to_ground_station(str("radio set sync"+sync + "\r\n", "utf-8"))
    if wait_for_ok() == true:
        print("value sucessfully set")
    else:
        print("invalid param error")

# set the preamble length between 0 and  65535
def radio_set_prlen(pr):
    if pr in range(0, 65535):
        write_to_ground_station(str("radio set pr"+pr + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")


# crc can only be set to true or false to enable error checking

def radio_set_crc(crc):
    if crc in ["on", "off"]:
        write_to_ground_station(str("radio set crc"+crc + "\r\n", "utf-8"))
        if wait_for_ok() == true:
            print("value sucessfully set")
        else:
            print("invalid param error")


def radio_set_rxmode():
    # set the timeout to 65535 the maximum amount
    write_to_ground_station(str("radio rx 65535", "utf-8"))
