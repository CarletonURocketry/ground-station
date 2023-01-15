# Emulates the RN2483 LoRa Radio Module
# Outputs emulated radio payloads from the CU-InSpace rocket
#
# Authors:
# Thomas Selwyn (Devil)

import random
import struct
import time
from multiprocessing import Process, Queue
from datetime import datetime


class SerialRN2483Emulator(Process):
    def __init__(self, serial_status: Queue, rn2483_radio_payloads: Queue):
        super().__init__()

        self.serial_status = serial_status

        self.rn2483_radio_payloads = rn2483_radio_payloads

        # Emulation Variables
        self.altitude = 0
        self.temp = 22
        self.going_up = True
        self.startup_time = datetime.now()

        self.run()

    def run(self):
        self.serial_status.put(f"rn2483_connected True")
        self.serial_status.put(f"rn2483_port test")

        while True:
            self.tester()
            time.sleep(random.uniform(0, 2000) / 1000)

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

        self.altitude += random.uniform(0, 4)

        packet_call_sign = b"Devils".hex()
        six_byte_spacer = b"      ".hex()  # Should be packet header data!!!
        packet_header = f"{packet_call_sign}{six_byte_spacer}"
        block_header = "840C0000"  # Should be struct generated header data!!!

        offset = datetime.now() - self.startup_time

        #self.rn2483_radio_payloads.put(f"{packet_header}{block_header}{'E01F00008D540100BC57FF0010FEFFFF'}")
        self.rn2483_radio_payloads.put(f"{packet_header}{block_header}{struct.pack('<Iiii', int(offset.total_seconds() * 1000), int(87181 + self.temp * 50), int(self.temp * 1000), int(self.altitude * 1000)).hex().upper()}")
