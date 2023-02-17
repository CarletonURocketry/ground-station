# Serial communication to the RN2483 LoRa Radio Module
# Outputs radio payloads from the CU-InSpace rocket
#
# Authors:
# Arsalan Syed
# Thomas Selwyn (Devil)
# Matteo Golin (liguini1)
# Zacchaeus Liang

# Imports
import time
import logging
from multiprocessing import Queue, Process
from typing import Optional
from serial import Serial, SerialException, EIGHTBITS, PARITY_NONE

# Constants
MODULATION_MODES: list[str] = ['lora', 'fsk']
POWER_MIN: int = -3
POWER_MAX: int = 16
VALID_SPREADING_FACTORS: list[int] = [7, 8, 9, 10, 11, 12]
VALID_CODING_RATES: list[str] = ["4/5", "4/6", "4/7", "4/8"]
VALID_BANDWIDTHS: list[int] = [125, 250, 500]
SYNC_MIN: int = 0
SYNC_MAX: int = 256
PREAMBLE_MIN: int = 0
PREAMBLE_MAX: int = 65535


# Radio process
class SerialRN2483Radio(Process):

    def __init__(
            self,
            serial_status: Queue,
            radio_signal_report: Queue,
            rn2483_radio_input: Queue,
            rn2483_radio_payloads: Queue,
            serial_port: str
    ):
        Process.__init__(self)

        self.serial_status = serial_status
        self.radio_signal_report = radio_signal_report
        self.rn2483_radio_input = rn2483_radio_input
        self.rn2483_radio_payloads = rn2483_radio_payloads

        self.serial_port = serial_port
        self.ser = None

        self.run()

    def run(self):
        while True:
            try:
                # initiate the USB serial connection
                logging.info(f"RN2483 Radio: Connecting to {self.serial_port}")
                # Settings matched to RN2483 Transceiver Data Sheet's default UART settings
                self.ser = Serial(port=self.serial_port,
                                  timeout=1,
                                  baudrate=57600,
                                  bytesize=EIGHTBITS,
                                  parity=PARITY_NONE,
                                  stopbits=1,
                                  rtscts=False)
                logging.info(f"RN2483 Radio: Connected to {self.serial_port}")
                self.serial_status.put(f"rn2483_connected True")
                self.serial_status.put(f"rn2483_port {self.serial_port}")

                self.init_rn2483_radio()
                self.set_rx_mode()

                while True:
                    while not self.rn2483_radio_input.empty():
                        self.write_to_rn2483_radio(self.rn2483_radio_input.get())
                        self.set_rx_mode()
                        # FUTURE TO DO LIMIT TO ONLY AFTER THE ENTIRE BATCH IS DONE.
                        # AFTER SENDING A COMMAND TO RADIO RECALL SET_RX_MODE()

                    self.check_for_transmissions()

            except SerialException:
                self.serial_status.put(f"rn2483_connected False")
                self.serial_status.put(f"rn2483_port null")
                logging.info("RN2483 Radio: Error communicating with serial device.")
                time.sleep(3)

    def _read_ser(self) -> str:
        """Read from serial line."""
        return str(self.ser.readline())

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

        logging.info("Successfully set GPIO.")

    def reset(self) -> bool:
        """Performs a software reset on the RN2483 radio."""

        self.write_to_rn2483_radio('sys reset')

        ret = self._read_ser()  # Confirm from the rn2483 radio that the reset was a success
        if 'RN2483' in ret:
            logging.info("Radio successfully reset.")
        return "RN2483" in ret

    def init_rn2483_radio(self):
        """
        Initializes the RN2483 radio with the default parameters.

        Should cyclic redundancy check (CRC) be enabled?
        Should image quality indicators (IQI) be enabled?
        """

        self.reset()  # Restart the radio module
        self.init_gpio()
        self.set_modulation("lora")
        self.set_frequency(433050000)
        self.set_power(15)
        self.set_spread_factor(9)
        self.set_coding_rate("4/7")
        self.set_bandwidth(500)
        self.set_preamble_len(6)
        self.set_cyclic_redundancy_check(True)
        self.set_iqi(False)
        self.set_sync_word(0x43)

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
        self.ser.flush()  # Flush the serial port

        self.ser.write(data.encode('utf-8'))  # Encode command_string as bytes and then transmit over serial port
        # Wait for response on the serial line. Return if 'ok' received
        # Sys reset gives us info about the board which we want to process differently from other commands
        if command_string not in ["sys reset", "radio get snr", "radio get rssi"]:
            # TODO: clean this up with read functions
            return self.wait_for_ok()
        elif command_string == 'radio get snr':
            self.radio_signal_report.put(f"snr {self._read_ser()}")

    def wait_for_ok(self) -> bool:
        """
        Check to see if 'ok' is loaded onto the serial line by the RN2483 radio. If we receive 'ok' then this
        function returns True. If anything else is read from the serial line then this function returns False.
        """

        rv = str(self.ser.readline())  # Read from serial line

        if 'ok' in rv:
            return True

        # Returned after mac pause command.
        if '4294967245' in rv:
            return True
        logging.error(f"wait_for_ok: {rv}")
        return False

    def set_frequency(self, frequency: int) -> bool:
        """Set the frequency of transmitted signals in Hz."""

        if not ((433050000 <= frequency <= 434790000) or (863000000 <= frequency <= 870000000)):  # TODO fix constants
            logging.error("Invalid frequency parameter.")
            return False

        success = self.write_to_rn2483_radio(f"radio set freq {frequency}")
        if success:
            logging.debug("Frequency successfully set.")
            return True

        logging.error("Frequency not set.")
        return False

    def set_modulation(self, modulation: str) -> None:
        """Set the modulation of the RN2483 radio."""

        if modulation not in MODULATION_MODES:
            logging.error("Setting modulation: either use fsk or lora.")
            return

        if self.write_to_rn2483_radio(f"radio set mod {modulation}"):
            logging.debug("Successfully set modulation.")
            return
        logging.error("Setting modulation.")

    def set_power(self, power: int) -> None:
        """
        Set power state between -3 and 15. The 15th state has an output power of 14.1 dBm for the 868 MHz band
        and 13.6dBm for the 433 MHz band.
        """

        if power not in range(POWER_MIN, POWER_MAX):
            logging.error("Invalid power parameter.")
            return

        if self.write_to_rn2483_radio(f"radio set pwr {power}"):
            logging.debug("Value power successfully set.")
            return
        logging.error("Power: radio unable to set.")

    def set_spread_factor(self, spread_factor: int) -> None:
        """
        Set the spreading factor for the rn2483 radio. Spreading factor can only be set to 7, 8, 9, 10, 11, or 12.
        A higher spreading factor means slower transmissions (symbols are more spread out). The system will have better
        reception and be less error-prone.
        """

        if spread_factor not in VALID_SPREADING_FACTORS:
            logging.error("Invalid spreading factor.")
            return

        if self.write_to_rn2483_radio(f"radio set sf {spread_factor}"):
            logging.debug("Value spreading factor successfully set.")
            return
        logging.error("Unable to set spreading factor.")

    def set_coding_rate(self, coding_rate: str) -> None:
        """
        Set coding rate. Coding rate can only be "4/5", "4/6", "4/7", "4/8
        Coding rate is the ratio of actual data to error-correcting data that is transmitted. Lower coding rate means a
        lower data rate.
        """

        # TODO Remove magic constants
        if coding_rate not in VALID_CODING_RATES:
            logging.error("Invalid cycling rate.")
            return

        if self.write_to_rn2483_radio(f"radio set cr {coding_rate}"):
            logging.debug("Value coding rate successfully set.")
            return
        logging.error("Coding rate: radio unable to set.")

    def set_bandwidth(self, bandwidth: int) -> None:
        """Set the bandwidth which can only be 125, 250 or 500Hz."""

        if bandwidth not in VALID_BANDWIDTHS:
            logging.error("Invalid receiving bandwidth.")
            return

        if self.write_to_rn2483_radio(f"Radio set bandwidth {bandwidth}"):
            logging.debug("Bandwidth successfully set.")
            return
        logging.error("Bandwidth: radio unable to set.")

    def set_iqi(self, iqi: bool) -> None:
        """Set invert IQ function on the RN2483 radio. IQI of True is 'on', False is 'off'."""

        iqi = "on" if iqi else "off"

        if self.write_to_rn2483_radio(f"radio set iqi {iqi}"):
            logging.debug("Value successfully set.")
            return
        logging.error("IQI: radio unable to set.")

    def set_sync_word(self, sync_word: hex) -> None:
        """Set the sync word of the RN2483 radio."""

        if int(sync_word, 16) not in range(SYNC_MIN, SYNC_MAX):
            logging.error("Invalid sync word.")
            return

        if self.write_to_rn2483_radio(f"Radio set sync {sync_word}"):
            logging.debug("Value sync word successfully set.")
            return
        logging.error("Sync parameter: radio unable to set.")

    def set_preamble_len(self, preamble_length: int) -> None:
        """
        Set the preamble length between 0 and 65535.
        Preamble means introduction. It's a transmission that is used to synchronize the receiver.
        """

        if preamble_length in range(PREAMBLE_MIN, PREAMBLE_MAX):
            logging.error("Invalid preamble length.")
            return

        if self.write_to_rn2483_radio(f"radio set prlen {preamble_length}"):
            logging.debug("Preamble length successfully set.")
            return
        logging.error("Unable to set preamble length.")

    def set_cyclic_redundancy_check(self, crc: bool) -> None:
        """
        Enable or disable the cyclic redundancy check. CRC of True is 'on', False is 'off'.
        CRC is used to detect errors in the received signal.
        """

        crc = "on" if crc else "off"

        success = self.write_to_rn2483_radio(f"radio set crc {crc}")
        if success:
            logging.debug("Value CRC successfully set.")
            return
        logging.error("CRC: radio unable to set.")

    def set_rx_mode(self) -> None:
        """Set the RN2483 radio so that it constantly listens for transmissions."""

        self.write_to_rn2483_radio("radio set wdt 0")  # Turn off watch dog timer
        self.write_to_rn2483_radio("mac pause")  # This command must be passed before any reception can occur

        if not self.write_to_rn2483_radio("radio rx 0"):  # Command radio to go into continuous reception mode
            logging.error("Failure putting radio into rx mode.")

    def check_for_transmissions(self) -> None:
        """Checks for new transmissions on the line."""

        message = str(self.ser.readline())

        if message == "b''":
            logging.info("Nothing received.")
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
            logging.error("Invalid transmission message.")
            return

        # Radio will send 'radio_tx_ok' when message has been transmitted
        i = 0
        while 'radio_tx_ok' not in str(self._read_ser()):
            time.sleep(0.1)  # If message not transmitted then wait for 1/10th of a second
            i += 1
            if i == 3:  # If we have waited 0.3 seconds, then stop waiting. Something has gone wrong.
                logging.error("Unable to transmit message.")
                return
        logging.debug("Successfully sent message.")
