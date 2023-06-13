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
from multiprocessing import Queue, Process
from typing import Optional
from serial import Serial, SerialException, EIGHTBITS, PARITY_NONE

from modules.misc.config import RadioParameters

# Constants
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


# Radio process
class SerialRN2483Radio(Process):
    def __init__(
        self,
        serial_status: Queue,
        radio_signal_report: Queue,
        rn2483_radio_input: Queue,
        rn2483_radio_payloads: Queue,
        serial_port: str,
        settings: RadioParameters,
    ):
        Process.__init__(self)

        self.serial_status = serial_status
        self.radio_signal_report = radio_signal_report
        self.rn2483_radio_input = rn2483_radio_input
        self.rn2483_radio_payloads = rn2483_radio_payloads

        self.serial_port = serial_port
        self.settings = settings

        self.run()

    def run(self):
        while True:
            try:
                # Settings matched to RN2483 Transceiver Data Sheet's default UART settings
                logger.info(f"RN2483 Radio: Connecting to {self.serial_port}")
                self.serial = Serial(
                    port=self.serial_port,
                    timeout=1,
                    baudrate=57600,
                    bytesize=EIGHTBITS,
                    parity=PARITY_NONE,
                    stopbits=1,
                    rtscts=False,
                )
                # initiate the USB serial connection
                logger.info(f"RN2483 Radio: Connected to {self.serial_port}")
                self.serial_status.put("rn2483_connected!")
                self.serial_status.put(f"rn2483_port {self.serial_port}")

                self.init_rn2483_radio()
                logger.debug("Radio initialization worked.")
                self.set_rx_mode()
                logger.debug("Rx mode set.")

                while True:
                    while not self.rn2483_radio_input.empty():
                        self.write_to_rn2483_radio(self.rn2483_radio_input.get())
                        self.set_rx_mode()
                        # FUTURE TO DO LIMIT TO ONLY AFTER THE ENTIRE BATCH IS DONE.
                        # AFTER SENDING A COMMAND TO RADIO RECALL SET_RX_MODE()

                    self.check_for_transmissions()

            except SerialException:
                self.serial_status.put("rn2483_connected False")
                self.serial_status.put("rn2483_port null")
                logger.info("RN2483 Radio: Error communicating with serial device.")
                time.sleep(3)

    def _read_ser(self) -> str:
        """Read from serial line."""
        return str(self.serial.readline())

    def init_gpio(self) -> None:
        """Set all GPIO pins to input mode, thereby putting them in a state of high impedance."""

        self.write_to_rn2483_radio("sys set pinmode GPIO0 digout")
        self.write_to_rn2483_radio("sys set pinmode GPIO1 digout")
        self.write_to_rn2483_radio("sys set pinmode GPIO2 digout")
        self.write_to_rn2483_radio("sys set pindig GPIO0 1")
        self.write_to_rn2483_radio("sys set pindig GPIO1 1")
        self.write_to_rn2483_radio("sys set pindig GPIO2 0")

        for i in range(0, 14):
            self.write_to_rn2483_radio(f"sys set pinmode GPIO{i} digin")

        logger.info("Successfully set GPIO.")

    def reset(self) -> bool:
        """Performs a software reset on the RN2483 radio."""

        self.write_to_rn2483_radio("sys reset")

        ret = self._read_ser()  # Confirm from the rn2483 radio that the reset was a success
        if "RN2483" in ret:
            logger.info("Radio successfully reset.")
        return "RN2483" in ret

    def init_rn2483_radio(self):
        """
        Initializes the RN2483 radio with the default parameters.

        Should cyclic redundancy check (CRC) be enabled?
        Should image quality indicators (IQI) be enabled?
        """

        # Restart the radio module
        self.reset()
        logger.info("Resetting radio...")

        # Initialize GPIO pins
        self.init_gpio()
        logger.info("Initializing GPIO...")

        # Setting parameters
        for parameter, value in self.settings:
            # Special case where spread factor value must be preceded by sf
            if parameter == "spread_factor":
                value = f"sf{value}"

            # Special case: boolean settings must be specified using on/off terms instead of true/false
            if parameter == "cyclic_redundancy" or parameter == "iqi":
                value = "on" if value else "off"

            if self.write_to_rn2483_radio(f"radio set {SETTING_KW[parameter]} {value}"):
                logger.debug(f"{parameter} successfully set to {value}.")
            else:
                logger.error(f"{parameter} could not be set to {value}.")

    def write_to_rn2483_radio(self, command_string: str) -> Optional[bool]:
        """
        Writes data to the RN2483 radio via UART.
        :author: Tarik
        :param command_string: The full command to be sent to the RN2483 radio

        >> write_to_rn2483_radio("radio set pwr 7")
        >> "ok"
        Above example sets the radio transmission power to 7
        """

        data = str(command_string)
        data += "\r\n"  # Must include carriage return for valid commands (see DS40001784B pg XX)
        self.serial.flush()  # Flush the serial port

        self.serial.write(data.encode("utf-8"))  # Encode command_string as bytes and then transmit over serial port
        # Wait for response on the serial line. Return if 'ok' received
        # Sys reset gives us info about the board which we want to process differently from other commands
        if command_string not in ["sys reset", "radio get snr", "radio get rssi"]:
            # TODO: clean this up with read functions
            return self.wait_for_ok()
        elif command_string == "radio get snr":
            self.radio_signal_report.put(f"snr {self._read_ser()}")

    def wait_for_ok(self) -> bool:
        """
        Check to see if 'ok' is loaded onto the serial line by the RN2483 radio. If we receive 'ok' then this
        function returns True. If anything else is read from the serial line then this function returns False.
        """

        rv = str(self.serial.readline())  # Read from serial line

        if "ok" in rv:
            return True

        # Returned after mac pause command.
        if "4294967245" in rv:
            return True
        logger.error(f"wait_for_ok: {rv}")
        return False

    def set_rx_mode(self) -> None:
        """Set the RN2483 radio so that it constantly listens for transmissions."""

        self.write_to_rn2483_radio("radio set wdt 0")  # Turn off watch dog timer
        self.write_to_rn2483_radio("mac pause")  # This command must be passed before any reception can occur

        if not self.write_to_rn2483_radio("radio rx 0"):  # Command radio to go into continuous reception mode
            logger.error("Failure putting radio into rx mode.")

    def check_for_transmissions(self) -> None:
        """Checks for new transmissions on the line."""

        message = str(self.serial.readline())
        logger.debug(f"serial message: {message}")

        if message == "b''":
            logger.info("Nothing received.")
            return

        message = message[10:-5]  # Trim unnecessary elements of the message
        self.rn2483_radio_payloads.put(message)  # Put serial message in data queue for telemetry

    def _tx(self, data) -> None:
        """
        Transmit data, a method used for debugging.
        ROCKET DOES NOT RESPOND TO TRANSMISSIONS AT THIS TIME.
        """

        self.write_to_rn2483_radio("mac pause")  # Command that must be called before each transmission and receive

        if not self.write_to_rn2483_radio(f"radio tx {data}"):  # Is the data we wish to transmit valid?
            logger.error("Invalid transmission message.")
            return

        # Radio will send 'radio_tx_ok' when message has been transmitted
        i = 0
        while "radio_tx_ok" not in str(self._read_ser()):
            time.sleep(0.1)  # If message not transmitted then wait for 1/10th of a second
            i += 1
            if i == 3:  # If we have waited 0.3 seconds, then stop waiting. Something has gone wrong.
                logger.error("Unable to transmit message.")
                return
        logger.debug("Successfully sent message.")
