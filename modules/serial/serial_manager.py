"""Handles connections, specifying what serial port a radio should use and spawning the serial processes."""

import glob
import sys
import logging
from queue import Queue
from multiprocessing import Process, active_children
from serial import Serial, SerialException
from modules.misc.config import Config
from modules.serial.serial_rn2483_radio import rn2483_radio_process
from modules.serial.serial_rn2483_emulator import SerialRN2483Emulator
from signal import signal, SIGTERM
from types import FrameType


# Set up logging
logger = logging.getLogger(__name__)


def shutdown_sequence(signum: int, stack_frame: FrameType):
    for child in active_children():
        child.terminate()
    exit(0)


def update_serial_ports(serial_status: Queue[str]) -> list[str]:
    """Finds and updates serial ports on device

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of the serial ports available on the system
    """
    com_ports: list[str] = [""]

    if sys.platform.startswith("win"):
        com_ports = ["COM%s" % (i + 1) for i in range(256)]
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        # '/dev/tty[A-Za-z]*'
        com_ports = glob.glob("/dev/ttyUSB*")
        com_ports += glob.glob("/dev/ACM*")
    elif sys.platform.startswith("darwin"):
        com_ports = glob.glob("/dev/tty.*")

    tested_com_ports: list[str] = []

    # Checks ports if they are potential COM ports
    for test_port in com_ports:
        try:
            ser = Serial(test_port)
            ser.close()
            tested_com_ports.append(test_port)
        except (OSError, SerialException):
            pass

    tested_com_ports.append("test")
    serial_status.put(f"serial_ports {tested_com_ports}")
    return tested_com_ports


class SerialManager:
    def __init__(
        self,
        serial_status: Queue[str],
        serial_ws_commands: Queue[list[str]],
        radio_signal_report: Queue[int],
        rn2483_radio_input: Queue[str],
        rn2483_radio_payloads: Queue[str],
        config: Config,
    ):
        self.serial_status: Queue[str] = serial_status
        self.serial_ports: list[str] = []
        self.serial_ws_commands: Queue[list[str]] = serial_ws_commands

        self.radio_signal_report: Queue[int] = radio_signal_report

        self.rn2483_radio_input: Queue[str] = rn2483_radio_input
        self.rn2483_radio_payloads: Queue[str] = rn2483_radio_payloads
        self.rn2483_radio: Process | None = None

        self.config = config

        # Immediately find serial ports
        self.serial_ports = update_serial_ports(self.serial_status)

        # Handle program closing to ensure no orphan processes
        signal(SIGTERM, shutdown_sequence)  # type:ignore

    def run(self):
        logger.info("Serial manager started.")

        while True:
            ws_cmd = self.serial_ws_commands.get()

            # Parse command
            try:
                match ws_cmd[0]:
                    case "rn2483_radio":
                        self.parse_rn2483_radio_ws(ws_cmd[1:])
                    case "update":
                        self.serial_ports = update_serial_ports(self.serial_status)
                    case _:
                        logger.error("Serial: Invalid device type.")
            except IndexError:
                logger.error("Serial: Error parsing ws command")

    def parse_rn2483_radio_ws(self, ws_cmd: list[str]) -> None:
        """Parses the websocket commands relating to the RN2483_radio"""
        radio_ws_cmd = ws_cmd[0]

        if radio_ws_cmd == "connect" and self.rn2483_radio is None:
            proposed_serial_port = ws_cmd[1]

            if proposed_serial_port == "test":
                self.rn2483_radio = Process(
                    target=SerialRN2483Emulator,
                    args=(self.serial_status, self.radio_signal_report, self.rn2483_radio_payloads),
                    daemon=True,
                )
            else:
                self.rn2483_radio = Process(
                    target=rn2483_radio_process,
                    args=(
                        self.serial_status,
                        self.radio_signal_report,
                        self.rn2483_radio_input,
                        self.rn2483_radio_payloads,
                        proposed_serial_port,
                        self.config.radio_parameters,
                    ),
                    daemon=True,
                )

            # Start the appropriate process (emulator or real radio)
            self.rn2483_radio.start()

        elif radio_ws_cmd == "connect":
            logger.info("Already connected.")

        elif radio_ws_cmd == "disconnect" and self.rn2483_radio is not None:
            logger.info("Serial: RN2483 Radio terminating")
            self.serial_status.put("rn2483_connected False")
            self.serial_status.put("rn2483_port null")
            self.rn2483_radio.terminate()
            self.rn2483_radio = None

        elif radio_ws_cmd == "disconnect":
            logger.warning("Serial: RN2483 Radio already disconnected.")
