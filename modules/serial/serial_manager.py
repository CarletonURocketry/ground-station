#
#
#
# Authors:
# Thomas Selwyn (Devil)
import glob
import threading
import sys

import time
from multiprocessing import Process, Queue, Value
from multiprocessing.shared_memory import ShareableList

from serial import Serial, SerialException

from modules.serial.serial_test import SerialTestClass



class SerialManager(Process):
    def __init__(self, serial_connected: Value, serial_connected_port: ShareableList, serial_ports: ShareableList,
                 serial_ws_commands: Queue, rn2483_radio_payloads: Queue):
        super().__init__()

        self.Serial_Test = None
        self.serial_ports = serial_ports
        self.serial = serial_connected
        self.serial_connected_port = serial_connected_port
        self.serial_ws_commands = serial_ws_commands
        self.rn2483_radio_payloads = rn2483_radio_payloads

        self.run()

    def run(self):
        while True:
            time.sleep(.1)

            ports = find_serial_ports()
            ports.append("test")
            for i in range(len(self.serial_ports)):
                self.serial_ports[i] = "" if i > len(ports) - 1 else str(ports[i])

            while not self.serial_ws_commands.empty():
                ws_cmd = self.serial_ws_commands.get()

                match ws_cmd[1]:
                    case "rn2483_radio":
                        self.parse_rn2483_radio_ws(ws_cmd)
                    case _:
                        print("Invalid serial device type.")




                    # Serial_Radio = Process(target=SerialManager, args=(rn2483_radio_input,
                    #                                                   rn2483_radio_payloads,
                    #                                                   rn2483_console_input,
                    #                                                   serial_connected, serial_connected_port, serial_ports))


    def parse_rn2483_radio_ws(self, ws_cmd):
        try:
            if ws_cmd[2] == "connect" and ws_cmd[3] == "test":
                if not self.serial.value:
                    self.Serial_Test = Process(target=SerialTestClass,
                                               args=(self.serial_ports, self.rn2483_radio_payloads), daemon=True)
                    self.Serial_Test.start()

                    self.serial.value = True
                    self.serial_connected_port[0] = "test"
                else:
                    print(f"Serial: Already connected.")

            if ws_cmd[2] == "disconnect":
                if self.serial.value:
                    print("Serial: RN2483 Payload Emulator terminating")
                    self.serial.value = False
                    self.serial_connected_port[0] = ""
                    self.Serial_Test.terminate()
                else:
                    print("Serial: Already disconnected.")
        except IndexError:
            print("Serial: Not enough arguments.")


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
    results = []
    for test_port in com_ports:
        try:
            s = Serial(test_port)
            s.close()
            results.append(test_port)
        except (OSError, SerialException):
            pass
    return results
