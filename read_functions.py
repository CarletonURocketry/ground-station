#
# commands for reading information from the ground station
# Author: Fahim
# editors: Arsalan

# Define Section

# the pins that we can read analog values from
VALID_ANALOG_PINS_RANGE1 = [i for i in range(1,4)]
VALID_ANALOG_PINS_RANGE2 = [i for i in range(5,14)]
VALID_ANALOG_PINS = VALID_ANALOG_PINS_RANGE1 + VALID_ANALOG_PINS_RANGE2

# the pins that we can read digital values from
VALID_DIGITAL_PINS = [i for i in range(14)]

class GroundStationReader():

    def __init__(self, serial, writer):
        """

        :param serial: a reference to the Serial::Serial object that is being used to communicate with the ground
                       station

        """

        self.ser = serial

    def read_frequency(self):
        """read the central frequency that the ground station is tuned to/transmitting at. If
           there is a problem reading the frequency, for example, if the ground station does not
           respond, or if it returns a string instead of a number, or it returns a frequency
           value that is not possible for the ground station, then returns -1"""

        freq = int(self.self.read_from_radio("freq"))

        # the lower (433 MHZ) freq range
        upper_1 = 434800000
        lower_1 = 433000000

        # the higher (866 MHZ) freq range
        upper_2 = 870000000
        lower_2 = 863000000

        if (upper_1 > freq > lower_1) or (upper_2 > freq > lower_2):
            return freq
        else:
            return -1

    def read_bitrate(self):
        """return the bit rate of the radio"""

        bitrate = int(self.read_from_radio("bitrate"))

        # the upper and lower limit values that the bit rate can take on
        upper_value = 65535
        lower_value = 0
        if lower_value < bitrate < upper_value:
            return bitrate
        else:
            return -1

    def read_bw(self):
        bw = int(self.read_from_radio("bw"))

        # the three possible values
        possibilities = [125, 250, 500]

        if bw in possibilities:
            return bw
        else:
            return -1

    def read_cr(self):
        cr = self.self.read_from_radio("cr")

        # the four possible strings
        possibilities = ['4/5', '4/6', '4/7', '4/8']

        if cr in possibilities:
            return cr
        else:
            return -1

    def read_bt(self):
        bt = self.read_from_radio("bt")

        # the four possible strings that could be returned
        possibilities = ['none', '1.0', '0.5', '0.3']
        if bt in possibilities:
            return bt
        else:
            return -1

    def read_crc(self):
        return self.read_from_radio("crc")

    def read_fdev(self):
        return self.read_from_radio("fdev")

    def read_afcbw(self):
        return self.read_from_radio("afcbw")

    def read_iqi(self):
        return self.read_from_radio("iqi")

    def read_mod(self):
        return self.self.read_from_radio("mod")

    def read_prlen(self):
        return self.read_from_radio("prlen")

    def read_pwr(self):
        return self.read_from_radio("pwr")

    def read_rssi(self):
        return self.read_from_radio("rssi")

    def read_rxbw(self):
        return self.read_from_radio("rxbw")

    def read_sf(self):
        return self.read_from_radio("sf")

    def read_snr(self):
        return self.read_from_radio("snr")

    def read_sync(self):
        return self.read_from_radio("sync")

    def read_wdt(self):
        return self.read_from_radio("wdt")

    # sys commands
    def read_ver(self):
        return self.read_from_radio("ver")

    def read_vdd(self):
        return self.read_from_radio("vdd")

    def read_hweui(self): 
        return self.read_from_radio("hweui")

    def read_nvm(self, address: str):
        """
        Accepts hexadecimal address from 300 to 3FF.
        """
        return self.read_from_radio("nvm " + address)

    def read_pin_dig(self, pin_name: str):
        """
        Accepts GPIO 0 - 13, UART_CTS, UART_RTS, TEST0-1.
        """

        if isinstance(pin_name, int):
            if pin_name in VALID_DIGITAL_PINS:
                pin_name = str(pin_name)
                return self.read_from_radio("pindig " + pin_name)

        return -1

    def read_pin_ana(self, pin_name: int):
        """
        reads the voltage value on a pin that has been set as an analog pin
        """

        if isinstance(pin_name, int):
            if pin_name in VALID_ANALOG_PINS:
                pin_name = str(pin_name)
                return self.read_from_radio("pinana GPIO" + pin_name)

        return -1

    @staticmethod
    def process_response(response: str):
        """
        Removes the carriage return and newline characters from the output received
        from the radio.


        @param  response: contains response from radio
        @return: the response received from radio in a clean format.
        will return -1 if error is found.

        examples:
        >>process_response("b'21313123321\r\n'")
        21313123321
        """
        # if we don't get a response
        if len(response) == 0:
            return -1
        if response == '\r\n':
            return -1

            # remove carriage return value
        return response.decode('UTF-8')[:-2]

    def read_from_radio(self, command: str):
        """reads data from the rn2483 via UART

       @param  command: command that will be written to ground station
       @return: the message received from station
                will return -1 if error is found
        """
        command = str(command)

        # split command into individual words if command is more than one word
        # long. Example:  'nvm 300'
        cmds = command.split()

        # these are parameters that require a 'sys' call. Ex. 'sys get vdd'
        sys_commands = ['vdd', 'nvm', 'ver', 'hweui', 'pindig', 'pinana']

        if cmds[0] in sys_commands:
            command = f"sys get {command}"

        # if parameter to be read is not covered by 'sys', it requires 'radio'
        else:
            command = f"radio get {command}"

        # flush the serial port
        self.ser.flush()

        # must include carriage return for valid commands (see DS40001784B pg XX)
        data = command + "\r\n"

        # encode command_string as bytes and then transmit over serial port
        self.ser.write(data.encode('utf-8'))

        # if command was received and valid, process it into an easy-to-use form.
        return self.process_response(self.ser.readline())
