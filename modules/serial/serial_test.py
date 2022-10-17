import multiprocessing
import random
import struct
import time
from multiprocessing import Process, Queue
from datetime import datetime

altitude = 0
temp = 22
going_up = True

class SerialTestClass(Process):
    def __init__(self, serial_input: Queue, serial_output: multiprocessing.Queue, COM_PORT="COM1"):
        super().__init__()

        self.SERIAL_PORT = COM_PORT
        self.serial_input = serial_input
        self.serial_output = serial_output


        # Continually add to these
        self.altitude = altitude
        self.temp = temp
        self.going_up = going_up


        self.startup_time = datetime.now()

        self.run()

    def run(self):
        #test_serial = serial.Serial(
            #port='COM1',
            #baudrate=115200,
            #parity=serial.PARITY_NONE,
            #stopbits=serial.STOPBITS_ONE,
            #bytesize=serial.EIGHTBITS,
            #timeout=0.1)

        while True:
            random_data = int(random.uniform(0, 1000))
            #print(f"SERIAL TEST: {random_data}")
            #self.serial_output.put(random_data)
            #print("Read from serial", test_serial.readline())

            #print("Read from serial b''")

            self.tester()
            #time.sleep(1)
            time.sleep(random.uniform(0, 2000)/1000)

    def tester(self):
        random_alternation = int(random.uniform(0, 1000))
        if self.going_up:
            self.temp += random_alternation / 500
        else:
            self.temp -= random_alternation / 500

        if self.temp > 100:
            self.going_up = False
        elif self.temp < 20:
            self.going_up = True

        self.altitude += random.uniform(0, 3)


        packet_call_sign = b"Devils".hex()
        six_byte_spacer = b"      ".hex() # Should be packet header data!!!
        packet_header = f"{packet_call_sign}{six_byte_spacer}"
        block_header = "840C0000"  # Should be struct generated header data!!!

        offset = datetime.now() - self.startup_time

        #self.serial_output.put(f"{packet_call_sign}{six_byte_spacer}{block_header}{'E01F00008D540100BC57FF0010FEFFFF'}")
        self.serial_output.put(f"{packet_header}{block_header}{struct.pack('<Iiii', int(offset.total_seconds() * 1000), int(87181 + self.temp*50), int(self.temp*1000), int(self.altitude*1000)).hex().upper()}")