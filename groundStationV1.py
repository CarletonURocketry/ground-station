# Ground station software for communication with the CU-InSpace rocket via an 
# RN2483 LoRa radio module.
# Authors: 

import serial as ser 

def init_ground_station():
    
    #notes from arsalan: why is there a space after every command (ex. "radio set pwr_"
    #does \r\n also work for ios systems?
    #does the radio always respond when we give it any command? Because then we can put the check_for_ok() function in the write() function

    # initlize a serial port  
    ser = serial.Serial(
                baudrate=57600,
                    # number of bits per bytes ((configure packet size?)
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,  # set parity check: no parity
                stopbits=0,  # number of stop bits
                rtscts=False,  # disable hardware (RTS/CTS) flow control
                    )  
   #set the frequency of the radio 
    ser.write(bytes(str("radio set freq 433050000") + "\r\n", "utf-8"))
    wait_for_ok()
    #set the power to -14 db
    ser.write(bytes(str("radio set pwr 14 ") + "\r\n", "utf-8"))
    wait_for_ok()
    #set the spreading factor
    ser.write(bytes(str("radio set sf sf9 ") + "\r\n", "utf-8"))
    wait_for_ok()
    
    #set the coding rate 
    ser.write(bytes(str("radio set cr 4/7 ") + "\r\n", "utf-8"))
    wait_for_ok()
    #set bandwdith
    ser.write(bytes(str("radio set bw 500 ") + "\r\n", "utf-8"))
    wait_for_ok()
    # set prlen preamble length
    ser.write(bytes(str("radio set prlen 6 ") + "\r\n", "utf-8"))
    wait_for_ok()
    # set crc
    ser.write(bytes(str("radio set crc on  ") + "\r\n", "utf-8"))
    wait_for_ok()
    #set iri
    ser.write(bytes(str("radio set  iqi off  ") + "\r\n", "utf-8"))
    wait_for_ok()
    #set sync word to be 0x43
    ser.write(bytes(str("radio set  sync 43  ") + "\r\n", "utf-8"))
    wait_for_ok()
    print("sucessfully configured lora radio")
   

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


def wait_for_ok():
    #comment from arsalan: if we never get an ok then this will turn into an infinite loop. Should set a timer of some sort.
    is_set=false 
    while is_set==false:
        ser.flush() # it is buffering. required to get the data out *now*
        
        rv = ser.readline()
        if rv == bytes('ok'): #wait untill it says ok
            is_set==true
    return true
