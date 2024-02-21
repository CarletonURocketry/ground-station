# Serial communication to the RN2483 LoRa Radio Module
# Outputs radio payloads from the CU-InSpace rocket
#
# Authors:
# Arsalan Syed
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)
# Zacchaeus Liang

# Imports
import time
import logging
from queue import Queue
from multiprocessing import Process
from typing import Optional
from serial import Serial, SerialException, EIGHTBITS, PARITY_NONE
from modules.misc.config import RadioParameters

RN2483_BAUD: int = 57600  # The baud rate of the RN2483 radio
NUM_GPIO: int = 14  # Number of GPIO pins on the RN2483 module

# Radio parameters
MODULATION_MODES: list[str] = ["lora", "fsk"]
POWER_MIN: int = -3
POWER_MAX: int = 16
VALID_SPREADING_FACTORS: list[int] = [7, 8, 9, 10, 11, 12]
VALID_CODING_RATES: list[str] = ["4/5", "4/6", "4/7", "4/8"]
VALID_BANDWIDTHS: list[int] = [125, 250, 500]
SYNC_MIN: int = 0
SYNC_MAX: int = 256
PREAMBLE_MIN: int = 0
PREAMBLE_MAX: int = 65535

# Keywords for parameter setting commands of the RN2483 module over serial
SETTING_KW: dict[str, str] = {
    "modulation": "mod",
    "frequency": "freq",
    "power": "pwr",
    "spread_factor": "sf",
    "coding_rate": "cr",
    "bandwidth": "bw",
    "preamble_len": "prlen",
    "cyclic_redundancy": "crc",
    "iqi": "iqi",
    "sync_word": "sync",
}

# Set up logger
logger = logging.getLogger(__name__)


# Helper functions
def wait_for_ok(conn: Serial) -> bool:
    """
    Check to see if 'ok' is loaded onto the serial line by the RN2483 radio. If we receive 'ok' then this
    function returns True. If anything else is read from the serial line then this function returns False.

    Arguments:
        conn: Serial connection to an RN2483 radio.
    """
    rv = str(conn.readline())  # Read from serial line
    return ("ok" in rv) or ("4294967245" in rv)


def radio_write(conn: Serial, data: str) -> None:
    """
    Writes data to the RN2483 radio via UART.

    Arguments:
        conn: A serial connection to the RN2483 radio.
        data: The full command or data to be sent to the RN2483 radio.
    """
    # Must include carriage return for valid commands (see DS40001784B pg XX)
    data = str(data) + "\r\n"
    conn.flush()  # Flush the serial port
    conn.write(data.encode("utf-8"))  # Encode command_string as bytes and then transmit over serial port


def radio_write_ok(conn: Serial, data: str) -> bool:
    """
    Writes a command to the radio and waits for a response of 'ok'.

    Arguments:
        conn: A serial connection to the radio.
        data: The full command or data to be sent to the RN2483 radio.
    """
    radio_write(conn, data)
    return wait_for_ok(conn)


class RN2483Radio(Process):
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

        # Connect to serial port
        self.serial = Serial(
            port=serial_port,
            timeout=1,
            baudrate=RN2483_BAUD,
            bytesize=EIGHTBITS,
            parity=PARITY_NONE,
            stopbits=1,
            rtscts=False,
        )

        logger.info(f"RN2483 Radio: Connected to {self.serial.port}")
        self.serial_status.put("rn2483_connected True")
        self.serial_status.put(f"rn2483_port {self.serial.port}")

        self.run()

    def run(self) -> None:
        """
        Runs the primary logic of the RN2483 radio.
        """

        # Set up radio
        while True:
            try:
                self.setup()
                logger.debug("Radio initialization worked.")
                self.set_rx_mode()
                logger.debug("Rx mode set.")
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

                # Commands that respond with success message
                if command_string not in ["sys reset", "radio get snr", "radio get rssi"]:
                    radio_write_ok(self.serial, command_string)

                # Signal to noise ratio request
                elif command_string == "radio get snr":
                    radio_write(self.serial, command_string)
                    self.radio_signal_report.put(f"snr {self.serial.readline()}")

                # All other requests
                radio_write(self.serial, command_string)

            self.set_rx_mode()
            # TODO: LIMIT TO ONLY AFTER THE ENTIRE BATCH IS DONE.
            # TODO: AFTER SENDING A COMMAND TO RADIO RECALL SET_RX_MODE()
            self.check_for_transmissions()

    def init_gpio(self) -> None:
        """Set all GPIO pins to input mode, thereby putting them in a state of high impedance."""

        radio_write(self.serial, "sys set pinmode GPIO0 digout")
        radio_write(self.serial, "sys set pinmode GPIO1 digout")
        radio_write(self.serial, "sys set pinmode GPIO2 digout")
        radio_write(self.serial, "sys set pindig GPIO0 1")
        radio_write(self.serial, "sys set pindig GPIO1 1")
        radio_write(self.serial, "sys set pindig GPIO2 0")

        for i in range(NUM_GPIO):
            radio_write(self.serial, f"sys set pinmode GPIO{i} digin")

        logger.info("Successfully set GPIO.")

    def reset(self) -> bool:
        """
        Performs a software reset on the RN2483 radio.

        Returns:
            True if the reset was successful, false otherwise.
        """
        radio_write(self.serial, "sys reset")
        wait_for_ok(self.serial)
        return "RN2483" in str(self.serial.readline())  # Confirm from the RN2483 radio that the reset was a success

    def setup(self):
        """
        Initializes the RN2483 radio with the default parameters.

        Should cyclic redundancy check (CRC) be enabled?
        Should image quality indicators (IQI) be enabled?
        """

        self.reset()  # Restart the radio module
        logger.info("Radio reset.")

        # Initialize GPIO pins
        self.init_gpio()
        logger.info("GPIO initialized.")

        # Setting parameters
        for parameter, value in self.settings:

            # Special case where spread factor value must be preceded by sf
            if parameter == "spread_factor":
                value = f"sf{value}"

            # Special case: boolean settings must be specified using on/off terms instead of true/false
            if parameter == "cyclic_redundancy" or parameter == "iqi":
                value = "on" if value else "off"

            if radio_write_ok(self.serial, f"radio set {SETTING_KW[parameter]} {value}"):
                logger.debug(f"{parameter} successfully set to {value}.")
            else:
                logger.error(f"{parameter} could not be set to {value}.")

    def set_rx_mode(self) -> bool:
        """
        Set the RN2483 radio to receive mode so that it constantly listens for transmissions.

        Returns:
            True setting receive mode worked, false otherwise.
        """
        if not radio_write_ok(self.serial, "radio set wdt 0"):  # Turn off watch dog timer
            return False
        if not radio_write_ok(self.serial, "mac pause"):  # This command must be passed before any reception can occur
            return False
        return radio_write_ok(self.serial, "radio rx 0")  # Command radio to go into continuous reception mode

    def check_for_transmissions(self) -> None:
        """Checks for new transmissions on the serial connection."""

        message = str(self.serial.readline())
        if message == "b''":
            logger.info("Nothing received.")
            return

        logger.debug(f"Received a serial message: {message}")
        message = message[10:-5]  # Trim unnecessary elements of the message
        logger.debug(f"Cleaned serial message: {message}")
        self.rn2483_radio_payloads.put(message)  # Put serial message in data queue for telemetry
