"""Process for controlling the setup of the RN2483 radio and reading its received messages."""

import time
import logging
from queue import Queue
from serial import SerialException
from modules.misc.config import RadioParameters
from modules.serial.rn2483_radio import RN2483Radio

logger = logging.getLogger(__name__)


def rn2483_radio_process(
    serial_status: Queue[str],
    radio_signal_report: Queue[int],
    rn2483_radio_input: Queue[str],
    rn2483_radio_payloads: Queue[str],
    serial_port: str,
    settings: RadioParameters,
):
    """Runs the primary logic for connecting to and reading from the RN2483 radio."""
    radio = RN2483Radio(serial_port)

    logger.info(f"RN2483 Radio: Connected to {serial_port}")
    serial_status.put("rn2483_connected True")
    serial_status.put(f"rn2483_port {serial_port}")

    # Set up radio
    while True:
        try:
            radio.setup(settings)
            logger.debug("Radio initialization worked.")
            break
        except SerialException:
            serial_status.put("rn2483_connected False")
            serial_status.put("rn2483_port null")
            logger.error("RN2483 Radio: Error communicating with serial device.")
            time.sleep(3)

    # Get transmissions
    while True:
        while not rn2483_radio_input.empty():
            command_string = rn2483_radio_input.get()
            if command_string == "radio get snr":
                radio_signal_report.put(radio.signal_report())
            else:
                logger.error(f"Radio command '{command_string}' is not implemented.")

        # TODO: LIMIT TO ONLY AFTER THE ENTIRE BATCH IS DONE.
        # TODO: AFTER SENDING A COMMAND TO RADIO RECALL SET_RX_MODE()

        # Put serial message in data queue for telemetry
        message = radio.receive()
        if message is not None:
            logger.info(f"Received: {message}")
            rn2483_radio_payloads.put(message)
