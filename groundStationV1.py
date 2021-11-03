# Ground station software for communication with the CU-InSpace rocket via an 
# RN2483 LoRa radio module.
# Authors: 

import serial

def init_ground_station():

    # initlize a serial port  
    ser = serial.Serial(
                    ser.baudrate=57600
                    # number of bits per bytes ((configure packet size?)
                    ser.bytesize=serial.EIGHTBITS
                    ser.parity=serial.PARITY_NONE  # set parity check: no parity
                    ser.stopbits=0  # number of stop bits
                    ser.rtscts=False  # disable hardware (RTS/CTS) flow control
                    ser.
                    )  
   #set the frequency of the radio 
    ser.write(bytes(str("radio set freq 433000000") + "\r\n", "utf-8"))




def write_to_ground_station(register:int):
    """writes data to the ground station via UART
       author: tarik, Fahim
       step 1: rudimentary write
       step 2: commands? 
       @param register:address of the register you want to write to"""
    


def read_from_ground_station(register:int):
    """reads data from the ground station via UART and puts it into the 
       correct data format to be passed onto the UI (check the logging format)
       author: elias 
       @param  register: address of register to read from
       @return data: the data that is stored in that register
    """
    

    
    
def load_map():
    """load in a map that can be used offline
        author: """
