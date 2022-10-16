import multiprocessing
import random
import time
from multiprocessing import Process, Queue
import serial


class SerialTestClass(Process):
    def __init__(self, serial_input: Queue, serial_output: multiprocessing.Queue, COM_PORT="COM1"):
        super().__init__()

        self.SERIAL_PORT = COM_PORT
        self.serial_input = serial_input
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
        payload = "446576696c73000000000000840C0000E01F00008D540100BC57000010FEFFFF"
        header = bytes.fromhex('840C0000')

        call_sign = b"Devils".hex()
        # print("Call sign -> ", call_sign)
        self.serial_output.put(payload)

        packet_callsign = "446576696c73"
        packet_callsignX = "446576696c73202020202020"


        packet_call_sign = b"Devils".hex()
        six_byte_spacer = b"      ".hex()
        block_header = "840C0000"
        block_altitude_rocket_on_fire = "E01F00008D540100BC57FF0010FEFFFF"
        block_altitude =                "E01F00008D540100BC44010020FF0600"
        block_altitude_zero =           "E01F00008D540100BC44010000000000"
        block_altitude_zero_fire =           "E01F00008D540100BC57FF0000000000"
        #time.sleep(5)
        print(f"BEST {packet_call_sign}{six_byte_spacer}{block_header}{block_altitude}")

        self.serial_output.put(f"{packet_call_sign}{six_byte_spacer}{block_header}{block_altitude_rocket_on_fire}")
        #time.sleep(1)
        self.serial_output.put(f"{packet_callsign}{six_byte_spacer}{block_header}{block_altitude_zero}")
        time.sleep(5)
        self.serial_output.put(f"{packet_callsignX}{block_header}{block_altitude_zero_fire}")
        time.sleep(2)
        self.serial_output.put(f"{packet_call_sign}{six_byte_spacer}{block_header}{block_altitude}")

        #self.serial_output.put(f"{packet_call_sign}{six_byte_spacer}")
        while True:
            random_data = int(random.uniform(0, 1000))
            #print(f"SERIAL TEST: {random_data}")
            #self.serial_output.put(random_data)
            #print("Read from serial", test_serial.readline())
            time.sleep(.2)
            #print("Read from serial b''")