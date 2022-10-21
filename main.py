# A Python-based ground station for collecting telemetry information from the CU-InSpace rocket.
# This data is collected using UART and is transmitted to the user interface using WebSockets.
#
# Authors:
# Thomas Selwyn (Devil)
import glob
import sys
import time
from multiprocessing import Queue, Process, Value
from multiprocessing.shared_memory import ShareableList

from serial import Serial, SerialException

from modules.misc.messages import printCURocket
from modules.serial.serial_rn2483_radio import SerialRN2483Radio
from modules.serial.serial_test import SerialTestClass
from modules.telemetry.telemetry import Telemetry
from modules.websocket.websocket import WebSocketHandler

rn2483_radio_input = Queue()
rn2483_radio_payloads = Queue()
rn2483_console_input = Queue()
rn2483_console_input_request = Queue()
telemetry_json_output = Queue()
ws_commands = Queue()

serial_connected = Value('i', False)
serial_connected_port = ShareableList([""])
serial_ports = ShareableList([""] * 8)


def main():
    printCURocket("Not a missile", "Lethal", "POWERED ASCENT")

    # Initialize Serial process to communicate with board
    # Incoming information comes directly from RN2483 LoRa radio module over serial UART
    # Outputs information in hexadecimal payload format to rn2483_radio_payloads
    Serial_Radio = Process(target=SerialRN2483Radio, args=(rn2483_radio_input,
                                                           rn2483_radio_payloads,
                                                           rn2483_console_input,
                                                           rn2483_console_input_request,
                                                           serial_connected, serial_connected_port, serial_ports))
    Serial_Radio.start()
    print("RN2483 Radio started")

    # Initialize Telemetry to parse radio packets, keep history and to log everything
    # Incoming information comes from rn2483_radio_payloads in payload format
    # Outputs information to telemetry_json_output in friendly json for UI
    telemetry = Process(target=Telemetry, args=(rn2483_radio_input, rn2483_console_input, rn2483_radio_payloads, telemetry_json_output,
                                                ws_commands, serial_connected, serial_connected_port, serial_ports))
    telemetry.daemon = True
    telemetry.start()
    print("Telemetry started")

    # Initialize Tornado websocket for UI communication
    # This is PURELY a pass through of data for connectivity. No format conversion is done here.
    # Incoming information comes from telemetry_json_output from telemetry
    # Outputs information to connected websocket clients
    websocket = Process(target=WebSocketHandler, args=(ws_commands, telemetry_json_output))
    websocket.daemon = True
    websocket.start()
    print("WebSocket started")

    # If a process requests a users input, this passes that through as subprocesses cannot use input().
    while True:
        # Continually checks for open serial ports, this is here because a serial port isn't specific to the rn2483.
        ports = find_serial_ports()
        ports.append("test")
        for i in range(len(serial_ports)):
            serial_ports[i] = "" if i > len(ports) - 1 else ports[i]
        # print(f"RN2483 Radio: {str(', ').join(ports)}")
        time.sleep(1)

        while not rn2483_console_input_request.empty():
            input_request = rn2483_console_input_request.get()

            if input_request == "TEST MODE":
                print("RN2483 Payload Emulator: Started")
                Serial_Test = Process(target=SerialTestClass, args=(rn2483_radio_input, rn2483_radio_payloads))
                Serial_Test.daemon = True
                Serial_Test.start()
            else:
                user_input = input(f"RN2483 Radio: {input_request}\n")
                rn2483_console_input.put(user_input)


def find_serial_ports() -> list[str]:
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """

    if sys.platform.startswith('win'):
        com_ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        com_ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        com_ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    # Checks ports if they are potential COM ports
    result = []
    for test_port in com_ports:
        try:
            s = Serial(test_port)
            s.close()
            result.append(test_port)
        except (OSError, SerialException):
            pass
    return result


if __name__ == '__main__':
    main()
