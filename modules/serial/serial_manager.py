# The unfortunate manager of serial ports
# Handles connections, specifying what serial port a radio should use and spawning the serial processes
#
# Authors:
# Thomas Selwyn (Devil)

import glob
import sys
import logging
from multiprocessing import Process, Queue, active_children
from serial import Serial, SerialException
from modules.misc.config import Config
from modules.serial.serial_rn2483_radio import SerialRN2483Radio
from modules.serial.serial_rn2483_emulator import SerialRN2483Emulator
from signal import signal, SIGTERM


# Set up logging
logger = logging.getLogger(__name__)


def shutdown_sequence():
    for child in active_children():
        child.terminate()
    exit(0)


class SerialManager(Process):
    def __init__(self, serial_status: Queue, serial_ws_commands: Queue, radio_signal_report: Queue,
                 rn2483_radio_input: Queue, rn2483_radio_payloads: Queue, config: Config):
        super().__init__()

        self.serial_status = serial_status
        self.serial_ports = []
        self.serial_ws_commands = serial_ws_commands

        self.radio_signal_report = radio_signal_report

        self.rn2483_radio_input = rn2483_radio_input
        self.rn2483_radio_payloads = rn2483_radio_payloads
        self.rn2483_radio = None

        self.config = config

        # Immediately find serial ports
        self.update_serial_ports()

        # Handle program closing to ensure no orphan processes
        signal(SIGTERM, shutdown_sequence)  # type:ignore

        self.run()

    def run(self):
        while True:
            while not self.serial_ws_commands.empty():
                ws_cmd = self.serial_ws_commands.get()
                self.parse_ws_command(ws_cmd)

    def parse_ws_command(self, ws_cmd):
        """ Parses the serial websocket commands """
        try:
            match ws_cmd[0]:
                case "rn2483_radio":
                    self.parse_rn2483_radio_ws(ws_cmd[1:])
                case "update":
                    self.update_serial_ports()
                case _:
                    logger.error("Serial: Invalid device type.")
        except IndexError:
            logger.error("Serial: Error parsing ws command")

    def parse_rn2483_radio_ws(self, ws_cmd):
        """ Parses the websocket commands relating to the rn2483_radio """
        radio_ws_cmd = ws_cmd[0]

        if radio_ws_cmd == "connect" and self.rn2483_radio is None:
            proposed_serial_port = ws_cmd[1]
            if proposed_serial_port != "test":
                self.rn2483_radio = Process(
                    target=SerialRN2483Radio,
                    args=(
                        self.serial_status,
                        self.radio_signal_report,
                        self.rn2483_radio_input,
                        self.rn2483_radio_payloads,
                        proposed_serial_port,
                        self.config.radio_parameters,
                    ),
                    daemon=True)
            else:
                self.rn2483_radio = Process(
                    target=SerialRN2483Emulator,
                    args=(
                        self.serial_status,
                        self.radio_signal_report,
                        self.rn2483_radio_payloads
                    ),
                    daemon=True)
            self.rn2483_radio.start()
        elif radio_ws_cmd == "connect":
            logger.info(f"Serial: Already connected.")
        elif radio_ws_cmd == "disconnect" and self.rn2483_radio is not None:
            logger.info(f"Serial: RN2483 Radio terminating")
            self.serial_status.put(f"rn2483_connected False")
            self.serial_status.put(f"rn2483_port null")
            self.rn2483_radio.terminate()
            self.rn2483_radio = None
        elif radio_ws_cmd == "disconnect":
            logger.warning("Serial: RN2483 Radio already disconnected.")

    def update_serial_ports(self) -> list[str]:
        """ Finds and updates serial ports on device

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        com_ports = [""]

        if sys.platform.startswith('win'):
            com_ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # '/dev/tty[A-Za-z]*'
            com_ports = glob.glob('/dev/ttyUSB*')
        elif sys.platform.startswith('darwin'):
            com_ports = glob.glob('/dev/tty.*')

        tested_com_ports = []

        # Checks ports if they are potential COM ports
        for test_port in com_ports:
            try:
                ser = Serial(test_port)
                ser.close()
                tested_com_ports.append(test_port)
            except (OSError, SerialException):
                pass

        tested_com_ports = tested_com_ports + ["test"]

        self.serial_ports = tested_com_ports
        self.serial_status.put(f"serial_ports {self.serial_ports}")

        return tested_com_ports
