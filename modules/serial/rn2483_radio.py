"""
Wrapper around RN2483 radio module.

See the command data sheet for more information:
https://ww1.microchip.com/downloads/en/DeviceDoc/RN2483-LoRa-Technology-Module-Command-Reference-User-Guide-DS40001784G.pdf
"""

from typing import Optional
from serial import Serial, EIGHTBITS, PARITY_NONE, SerialException
from modules.misc.config import RadioParameters

RN2483_BAUD: int = 57600  # The baud rate of the RN2483 radio
NUM_GPIO: int = 14  # Number of GPIO pins on the RN2483 module
READ_TIMEOUT: float = 10.0  # Time out for serial read operations

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
    data += "\r\n"
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


class RN2483Radio:
    def __init__(self, serial_port: str):
        self.serial = Serial(
            port=serial_port,
            baudrate=RN2483_BAUD,
            bytesize=EIGHTBITS,
            parity=PARITY_NONE,
            stopbits=1,
        )
        self.serial.timeout = READ_TIMEOUT  # Read timeout

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

    def reset(self) -> bool:
        """
        Performs a software reset on the RN2483 radio.

        Returns:
            True if the reset was successful, false otherwise.
        """
        radio_write(self.serial, "sys reset")
        wait_for_ok(self.serial)
        return "RN2483" in str(self.serial.readline())  # Confirm from the RN2483 radio that the reset was a success

    def configure(self, parameters: RadioParameters) -> None:
        """
        Configures the RN2483 radio with the provided radio parameters.

        Arguments:
            parameters: The parameters to set the radio with.

        Raises:
            SerialException: When a radio parameter could not be set.
        """

        for parameter, value in parameters:
            # Special case where spread factor value must be preceded by sf
            if parameter == "spread_factor":
                value = f"sf{value}"

            # Special case: boolean settings must be specified using on/off terms instead of true/false
            if parameter == "cyclic_redundancy" or parameter == "iqi":
                value = "on" if value else "off"

            if not radio_write_ok(self.serial, f"radio set {SETTING_KW[parameter]} {value}"):
                raise SerialException(f"Could not set parameter '{SETTING_KW[parameter]}' to '{value}'.")

    def setup(self, parameters: RadioParameters) -> None:
        """
        Resets the RN2483 radio, initializes its GPIO pins and sets its parameters to those provided.

        Arguments:
            parameters: The parameters to set up the radio with.

        Raises:
            SerialException: When a radio parameter could not be set.
        """
        self.reset()
        self.configure(parameters)
        if not radio_write_ok(self.serial, "radio set wdt 0"):  # Turn off watch dog timer
            raise SerialException("Could not turn off watchdog timer.")
        # For some reason, initializing GPIO causes issues. We don't need them anyway
        # self.init_gpio()

    def _set_rx_mode(self) -> bool:
        """
        Set the RN2483 radio to receive mode so that it constantly listens for transmissions.

        Returns:
            True setting receive mode worked, false otherwise.
        """
        if not radio_write_ok(self.serial, "mac pause"):  # This command must be passed before any reception can occur
            return False

        # Command radio to go into continuous reception mode
        radio_write(self.serial, "radio rx 0")
        result = str(self.serial.readline())
        if "busy" in result or "ok" in result:
            return True
        return False

    def receive(self) -> Optional[str]:
        """
        Checks for new transmissions on the serial connection.

        Returns:
            A string message that the radio received (in hexadecimal digits), otherwise None.
        """

        # Enter receive mode
        if not self._set_rx_mode():
            return None

        message = str(self.serial.readline())[10:-5]  # Trim off reception indicator

        # Check if message is in hex
        try:
            int(message, 16)
            return message
        except ValueError:
            return None

    def signal_report(self) -> int:
        """
        Gets a signal to noise ratio report from the radio.

        Returns:
            An integer from -128 to 127 representing the signal to noise ratio of the last received packet.
        """
        radio_write(self.serial, "radio get snr")
        return int(self.serial.readline())
