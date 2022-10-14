import multiprocessing
import random
import time
from multiprocessing import Process, Queue
import serial


class SerialTestClass(Process):
    def __init__(self, SERIAL_PORT, serial_output: Queue):
        super().__init__()

        # self.serial_input = serial_input
        self.SERIAL_PORT = SERIAL_PORT
        self.serial_output = serial_output

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
            print(f"SERIAL TEST: {random_data}")
            self.serial_output.put(random_data)
            #print("Read from serial", test_serial.readline())
            time.sleep(0.2)
            print("Read from serial b''")