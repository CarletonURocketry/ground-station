import multiprocessing
import time
from abc import ABC

from modules.misc.messages import printCURocket
from modules.serial.serial_test import SerialTestClass
from modules.telemetry.telemetry import Telemetry
from modules.websocket.websocket import WebSocketHandler

serial_input = multiprocessing.Queue()
serial_data_output = multiprocessing.Queue()
telemetry_json_output = multiprocessing.Queue()
websocket_commands = multiprocessing.Queue()


class GroundStation(ABC):


    def main(self):
        printCURocket("Not a missile", "Lethal", "POWERED ASCENT")

        # Initialize Serial process to communicate with board
        # Incoming information comes directly from RN2483 LoRa radio module over serial UART
        # Outputs information in packet format to serial_data_output
        serial_driver = multiprocessing.Process(target=SerialTestClass, args=(serial_input, serial_data_output, "COM1"))
        serial_driver.daemon = True
        serial_driver.start()
        print("Serial started")

        # Initialize Telemetry to parse radio packets, keep history and to log everything
        # Incoming information comes from serial_data_output in payload format
        # Outputs information to telemetry_json_output in friendly json for UI
        telemetry = multiprocessing.Process(target=Telemetry,
                                            args=(serial_input, serial_data_output, telemetry_json_output))
        telemetry.daemon = True
        telemetry.start()
        print("Telemetry started")

        # Initialize Tornado websocket for UI communication
        # This is PURELY a pass through of data for connectivity. No format conversion is done here.
        # Incoming information comes from telemetry_json_output from telemetry
        # Outputs information to connected websocket clients
        websocket = multiprocessing.Process(target=WebSocketHandler, args=(websocket_commands, telemetry_json_output))
        websocket.daemon = True
        websocket.start()
        print("WebSocket started")


        # Make this into a console input device to change parameters?
        # Randomly spitting out queue data
        i = 0
        while True:
            i = i + 1
            time.sleep(5)
            # print(serial_output.get())
            # while not serial_data_output.empty():
            # print(f"MAIN THREAD READING SERIAL OUTPUT QUEUE: {serial_data_output.get()}")


if __name__ == '__main__':
    GroundStation().main()
