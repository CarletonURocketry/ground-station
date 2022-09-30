# Ground station software for communication with the CU-InSpace rocket via an
# RN2483 LoRa radio module.
# Authors:
# 

import time
import threading
import sys
import glob
from typing import Tuple, List

import serial

import serial
import queue
import packets
import UI_functions

from read_functions import *
from ConfigureFunctions import *


class GroundStation:

    def __init__(self, com_port='COM4'):

        # initiate the USB serial connection
        self.ser = serial.Serial(port=com_port,
                                 timeout=1,
                                 baudrate=57600,
                                 # number of bits per message
                                 bytesize=serial.EIGHTBITS,
                                 # set parity check: no parity
                                 parity=serial.PARITY_NONE,
                                 # number of stop bits
                                 stopbits=1,
                                 # disable hardware (RTS/CTS) flow control
                                 rtscts=False)

    def _read_ser(self):
        # read from serial line
        rv = str(self.ser.readline())

        return rv

    def init_gpio(self):
        """set all GPIO pins to input mode, thereby putting them in a state of high impedence"""

        self.write_to_ground_station("sys set pinmode GPIO0 digout")
        self.write_to_ground_station("sys set pinmode GPIO1 digout")
        self.write_to_ground_station("sys set pinmode GPIO2 digout")
        self.write_to_ground_station("sys set pindig GPIO0 1")
        self.write_to_ground_station("sys set pindig GPIO1 1")
        self.write_to_ground_station("sys set pindig GPIO2 0")

        self.write_to_ground_station("sys set pinmode GPIO3 digin")
        self.write_to_ground_station("sys set pinmode GPIO4 digin")
        self.write_to_ground_station("sys set pinmode GPIO5 digin")
        self.write_to_ground_station("sys set pinmode GPIO6 digin")
        self.write_to_ground_station("sys set pinmode GPIO5 digin")
        self.write_to_ground_station("sys set pinmode GPIO6 digin")
        self.write_to_ground_station("sys set pinmode GPIO7 digin")
        self.write_to_ground_station("sys set pinmode GPIO8 digin")
        self.write_to_ground_station("sys set pinmode GPIO9 digin")
        self.write_to_ground_station("sys set pinmode GPIO10 digin")
        self.write_to_ground_station("sys set pinmode GPIO11 digin")
        self.write_to_ground_station("sys set pinmode GPIO12 digin")
        self.write_to_ground_station("sys set pinmode GPIO13 digin")

        print('successfully set GPIO')

    def reset(self):
        """perform a software reset on the ground station"""

        self.write_to_ground_station('sys reset')

        # confirm from the ground station that the reset was a success
        ret = self._read_ser()

        if 'RN2483' in ret:
            print('radio successfully reset')
            return True
        else:
            return False

    def init_ground_station(self):
        """initialize the ground station with default parameters for the following parameters:
           radio frequency: the frequency of the signal the radio uses to communicate with
           power: the power of the signal (output)
           spreading factor:
           bandwidth:
           length of preamble 
           should cyclic redundancy check (CRC) be enabled?
           should image quality indicators (IQI) be enabled?
           setting the sync word
           
        """
        # restart the radio module
        self.reset()

        # initilize all the pins to be inputs
        self.init_gpio()

        # set modulation type to lora
        self.set_mod('lora')

        # set the frequency of the radio (Hz)
        self.set_freq(433050000)

        # set the transmission power to 15 db (max POWARRRR)
        self.set_pwr(14)

        # set the transmission spreading factor. The higher the spreading factor,
        # the slower the transmissions (symbols are spread out more) and the better
        # the reception and error prone the system is.
        self.set_sf(9)

        # set the coding rate (ratio of actual data to error-correcting data that
        # is transmitted. The lower the coding rate the lower the data rate.
        self.set_cr("4/7")

        # set reception bandwidth. This should match the transmission bandwidth of the 
        # node that this ground station is trying to recieve.
        # self.set_rxbw(500)

        # set the length of the preamble. Preamble means introduction. It's a 
        # transmission that is used to synchronize the reciever.
        self.set_prlen(6)

        # set cyclic redundancy check on/off. This is used to detect errors
        # in the recieved signal
        self.set_crc("on")

        # set the invert IQ function
        self.set_iqi("off")

        # set sync word to be 0x43
        self.set_sync("43")

    def write_to_ground_station(self, command_string):
        """writes data to the ground station via UART
        author: Tarik
        @param command_string: full command to be send to the ground station
        @param COM_PORT: the COM port to be used for the UART transmission
        
        Ex.
        >>write_to_ground_station("radio set pwr 7", COM1)
        >>"ok"
        
        //above example sets the radio tramission power to 7 using COM1
        
        """

        data = str(command_string)

        # flush the serial port
        self.ser.flush()

        # must include carriage return for valid commands (see DS40001784B pg XX)
        data = data + "\r\n"

        # encode command_string as bytes and then transmit over serial port
        self.ser.write(data.encode('utf-8'))

        # wait for response on the serial line. Return if 'ok' received
        # sys reset gives us info about the board which we want to process differently from other commands
        if command_string != 'sys reset':
            return self.wait_for_ok()

    def load_map(self):
        """load in a map that can be used offline
            author: """

    def _tx(self, data):
        """transmit data, a method used for debugging"""

        # command that must be called before each transmission and recieve
        self.write_to_ground_station("mac pause")

        # is the data we wish to transmit valid?
        valid = self.write_to_ground_station("radio tx " + data)

        if not valid:
            print('invalid transmission message')
            return

        else:
            i = 0

            # radio will send 'radio_tx_ok' when message has been transmitted
            while 'radio_tx_ok' not in str(self._read_ser()):

                # if message not transmitted then wait for 1/10th of a second
                time.sleep(0.1)

                i += 1

                # if we have waited 0.3 seconds, then stop waiting. something 
                # has gone wrong. 
                if i == 3:
                    print('unable to transmit message')
                    return

            print('successfully sent mesage')


def serial_ports() -> tuple[list[str], list[str]]:
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    # Checks ports if they are potential COM ports
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return ports, result


# for debugging

if __name__ == '__main__':
    ports, results = serial_ports()
    print("DEBUG All Ports:", ports)
    print("%s ports found. " % len(ports))
    print("Possible COM Serial Ports:", results)

    if len(results) > 1:
        # rx = GroundStation('/dev/ttyUSB1')
        tx = GroundStation('/dev/ttyUSB0')
        # xxxxxxxxxxxxxxxxxxxxxtx.init_ground_station()

        # rx.init_ground_station()
        tx.init_ground_station()
        tx.write_to_ground_station('radio set bw 500')

        # rx.write_to_ground_station('radio rx 0')
        # tx.write_to_ground_station('radio rx 1')

        # rx.set_rxmode()
        # rx.write_to_ground_station('radio set wdt 0')
        # rx.write_to_ground_station('mac pause')
        # rx.write_to_ground_station('radio rx 0')

        # tx.write_to_ground_station('mac pause')
        # tx.write_to_ground_station('radio set pwr 10')
        # tx.write_to_ground_station('radio tx 1234562')

        print('_____________________________________')
        q = queue.Queue()
        tx.set_rx_mode(q)
