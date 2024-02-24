"""Process for controlling the setup of the RN2483 radio and reading its received messages."""

import time
import logging
from queue import Queue
from multiprocessing import Process
from serial import SerialException
from modules.misc.config import RadioParameters
from modules.serial.rn2483_radio import RN2483Radio

logger = logging.getLogger(__name__)


# Helper functions
class RN2483RadioProcess(Process):
    def __init__(
        self,
        serial_status: Queue[str],
        radio_signal_report: Queue[str],
        rn2483_radio_input: Queue[str],
        rn2483_radio_payloads: Queue[str],
        serial_port: str,
        settings: RadioParameters,
    ):
        super().__init__()
        self.serial_status: Queue[str] = serial_status
        self.radio_signal_report: Queue[str] = radio_signal_report
        self.rn2483_radio_input: Queue[str] = rn2483_radio_input
        self.rn2483_radio_payloads: Queue[str] = rn2483_radio_payloads
        self.settings = settings

        self.radio = RN2483Radio(serial_port)

        logger.info(f"RN2483 Radio: Connected to {serial_port}")
        self.serial_status.put("rn2483_connected True")
        self.serial_status.put(f"rn2483_port {serial_port}")

        self.run()

    def run(self) -> None:
        """
        Runs the primary logic for connecting to and reading from the RN2483 radio.
        """

        # Set up radio
        while True:
            try:
                self.radio.setup(self.settings)
                logger.debug("Radio initialization worked.")
                break
            except SerialException:
                self.serial_status.put("rn2483_connected False")
                self.serial_status.put("rn2483_port null")
                logger.info("RN2483 Radio: Error communicating with serial device.")
                time.sleep(3)

        # Get transmissions
        while True:
            while not self.rn2483_radio_input.empty():

                command_string = self.rn2483_radio_input.get()
                if command_string == "radio get snr":
                    self.radio_signal_report.put(str(self.radio.signal_report()))  # TODO: change string to integer
                else:
                    logger.error(f"Radio command '{command_string}' is not implemented.")

            # TODO: LIMIT TO ONLY AFTER THE ENTIRE BATCH IS DONE.
            # TODO: AFTER SENDING A COMMAND TO RADIO RECALL SET_RX_MODE()

            # Put serial message in data queue for telemetry
            message = self.radio.receive()
            if message is not None:
                logger.info(message)
                self.rn2483_radio_payloads.put(message)
