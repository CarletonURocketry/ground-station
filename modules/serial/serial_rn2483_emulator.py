# Emulates the RN2483 LoRa Radio Module
# Outputs emulated radio payloads from the CU-InSpace rocket
#
# Authors:
# Thomas Selwyn (Devil)

import random
import struct
import time
from queue import Queue
from multiprocessing import Process
from datetime import datetime


class SerialRN2483Emulator(Process):
    def __init__(self, serial_status: Queue[str], radio_signal_report: Queue[str], rn2483_radio_payloads: Queue[str]):
        super().__init__()

        self.serial_status: Queue[str] = serial_status

        self.rn2483_radio_payloads: Queue[str] = rn2483_radio_payloads
        self.radio_signal_report: Queue[str] = radio_signal_report

        # Emulation Variables
        self.altitude: float = 0
        self.temp: float = 22
        self.going_up: bool = True
        self.startup_time: datetime = datetime.now()

        self.run()

    def run(self):
        self.serial_status.put("rn2483_connected True")
        self.serial_status.put("rn2483_port test")
        self.radio_signal_report.put("snr 30")
        # self.radio_signal_report.put("rssi -55")
        while True:
            self.tester()
            time.sleep(random.uniform(0, 2000) / 100000)

    def tester(self):
        """Generates test data to give to the telemetry process"""
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

        # self.rn2483_radio_payloads.put(f"{packet_header}{block_header}{'E01F00008D540100BC57FF0010FEFFFF'}")
        formatted_secs = int(offset.total_seconds() * 1000)
        formatted_temp = int(87181 + self.temp * 50)
        formatted_temp2 = int(self.temp * 1000)
        formatted_alt = int(self.altitude * 1000)
        byte_contents = struct.pack("<Iiii", formatted_secs, formatted_temp, formatted_temp2, formatted_alt)
        self.rn2483_radio_payloads.put(f"{packet_header}{block_header}{byte_contents.hex().upper()}")
