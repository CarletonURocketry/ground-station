# Serial communication to the RN2483 LoRa Radio Module
# Outputs radio payloads from the CU-InSpace rocket
#
# Authors:
# Arsalan Syed
# Thomas Selwyn (Devil)
# Zacchaeus Liang

import glob
import sys
import queue
import time

from serial import Serial, SerialException, EIGHTBITS, PARITY_NONE
from multiprocessing import Queue, Process


class SerialRN2483Radio(Process):

    def __init__(self, rn2483_radio_input: Queue, rn2483_radio_payloads: Queue, console_input: Queue,
                 console_input_request: Queue):
        Process.__init__(self)

        self.rn2483_radio_input = rn2483_radio_input
        self.rn2483_radio_payloads = rn2483_radio_payloads

        self.console_input = console_input
        self.console_input_request = console_input_request

        self.serial_port = None
        self.ser = None

        self.run()

    def run(self):
        while True:
            available_ports = serial_ports()[1]
            available_ports.append("test")
            print(f"RN2483 Radio: {str(', ').join(available_ports)}")

            self.console_input_request.put("WHAT PORT?")

            waiting_for_user_input = True

            while waiting_for_user_input:
                while not self.console_input.empty():
                    waiting_for_user_input = False
                    user_input = self.console_input.get()

                    if user_input == "test":
                        self.console_input_request.put("TEST MODE")
                        print("RN2483 Radio: Serial link disabled due to enabling test mode.")
                        return
                    else:
                        self.serial_port = user_input.upper()

            try:
                # initiate the USB serial connection
                print(f"RN2483 Radio: Connecting to {self.serial_port}")
                self.ser = Serial(port=self.serial_port,
                                  timeout=1,
                                  baudrate=57600,
                                  # number of bits per message
                                  bytesize=EIGHTBITS,
                                  # set parity check: no parity
                                  parity=PARITY_NONE,
                                  # number of stop bits
                                  stopbits=1,
                                  # disable hardware (RTS/CTS) flow control
                                  rtscts=False)
                print(f"RN2483 Radio: Connected to {self.serial_port}")
                self.init_rn2483_radio()
                q = queue.Queue()
                self.set_rx_mode(q)

            except SerialException:
                print("RN2483 Radio: Error communicating with serial device.")

    def _read_ser(self):
        # read from serial line
        rv = str(self.ser.readline())

        return rv

    def init_gpio(self):
        """set all GPIO pins to input mode, thereby putting them in a state of high impedance"""

        self.write_to_rn2483_radio("sys set pinmode GPIO0 digout")
        self.write_to_rn2483_radio("sys set pinmode GPIO1 digout")
        self.write_to_rn2483_radio("sys set pinmode GPIO2 digout")
        self.write_to_rn2483_radio("sys set pindig GPIO0 1")
        self.write_to_rn2483_radio("sys set pindig GPIO1 1")
        self.write_to_rn2483_radio("sys set pindig GPIO2 0")

        for i in range(0, 14):
            self.write_to_rn2483_radio(f"sys set pinmode GPIO{i} digin")

        print('successfully set GPIO')

    def reset(self):
        """perform a software reset on the rn2483 radio"""

        self.write_to_rn2483_radio('sys reset')

        # confirm from the rn2483 radio that the reset was a success
        ret = self._read_ser()

        if 'RN2483' in ret:
            print('radio successfully reset')
            return True
        else:
            return False

    def init_rn2483_radio(self):
        """initialize the rn2483 radio with default parameters for the following parameters:
           radio frequency: the frequency of the signal the radio uses to communicate with
           power: the power of the signal (output)
           spreading factor:
           bandwidth:
           length of preamble
           should cyclic redundancy check (CRC) be enabled?
           should image quality indicators (IQI) be enabled?
           setting the sync word
        """

        # restart the radio module
        self.reset()

        # initialize all the pins to be inputs
        self.init_gpio()

        # set modulation type to lora
        self.set_mod('lora')

        # set the frequency of the radio (Hz)
        self.set_freq(433050000)

        # set the transmission power to 15 db (max POWARRRR)
        self.set_pwr(14)

        # set the transmission spreading factor. The higher the spreading factor,
        # the slower the transmissions (symbols are spread out more) and the better
        # the reception and error-prone the system is.
        self.set_sf(9)

        # set the coding rate (ratio of actual data to error-correcting data) that
        # is transmitted. The lower the coding rate the lower the data rate.
        self.set_cr("4/7")

        # set radio bandwidth.
        self.set_bw(500)

        # set the length of the preamble. Preamble means introduction. It's a
        # transmission that is used to synchronize the receiver.
        self.set_prlen(6)

        # set cyclic redundancy check on/off. This is used to detect errors
        # in the received signal
        self.set_crc("on")

        # set the invert IQ function
        self.set_iqi("off")

        # set sync word to be 0x43
        self.set_sync("43")

    def write_to_rn2483_radio(self, command_string):
        """writes data to the rn2483 radio via UART
        author: Tarik
        @param command_string: full command to be sent to the rn2483 radio

        Ex.
        >>write_to_rn2483_radio("radio set pwr 7")
        >>"ok"

        //above example sets the radio transmission power to 7

        """

        data = str(command_string)

        # flush the serial port
        self.ser.flush()

        # must include carriage return for valid commands (see DS40001784B pg XX)
        data = data + "\r\n"

        # encode command_string as bytes and then transmit over serial port
        self.ser.write(data.encode('utf-8'))

        # wait for response on the serial line. Return if 'ok' received
        # sys reset gives us info about the board which we want to process differently from other commands
        if command_string != 'sys reset' and command_string != 'radio get snr' and command_string != 'radio get rssi':
            # TODO: clean this up with read functions
            return self.wait_for_ok()

    def wait_for_ok(self):
        """
        Check to see if 'ok' is loaded onto the serial line by the rn2483 radio. If we receive 'ok' then this
        function returns True. If anything else is read from the serial line then this function returns False.
        """

        # read from serial line
        rv = str(self.ser.readline())

        if 'ok' in rv:
            return True

        elif rv != 'ok':
            # returned after mac pause command.
            if '4294967245' in rv:
                return True

            print('error: wait_for_ok: ' + rv)

            return False

    def set_freq(self, freq):
        """set the frequency of transmitted signals"""

        if not ((433050000 <= freq <= 434790000) or (863000000 <= freq <= 870000000)):
            print('invalid frequency parameter.')
            return False

        success = self.write_to_rn2483_radio("radio set freq " + str(freq))
        if success:
            print("frequency successfully set")
            return True
        else:
            print("error: frequency not set")
            return False

    def set_mod(self, mod):

        if mod in ['lora', 'fsk']:
            success = self.write_to_rn2483_radio('radio set mod ' + mod)
            if success:
                print('successfully set modulation')
            else:
                print('error setting modulation')
        else:
            print('error setting modulation: either use fsk or lora')

    def set_pwr(self, pwr):
        """ set power possible values between -3 and 14 db"""
        # TODO: FIGURE OUT MAX POWER
        if pwr in range(-3, 16):

            success = self.write_to_rn2483_radio("radio set pwr " + str(pwr))
            if success:
                print("value power successfully set")
                return

            else:
                print("power error:radio unable to set")
                return

        print("invalid power param")
        return

    def set_sf(self, sf):
        """set the spreading factor for the rn2483 radio. Spreading factor
           can only be set to 7, 8, 9, 10, 11, or 12.

        """

        if sf in [7, 8, 9, 10, 11, 12]:
            success = self.write_to_rn2483_radio("radio set sf sf" + str(sf))
            if success:
                print("value spreading factor successfully set")
                return
            else:
                print("ERROR: unable to set spreading factor")
                return

        print("ERROR: invalid spreading factor")
        return

    def set_cr(self, cr):
        """set coding rate which can only be "4/5", "4/6", "4/7", "4/8"""

        if cr in ["4/5", "4/6", "4/7", "4/8"]:
            success = self.write_to_rn2483_radio("radio set cr " + str(cr))
            if success:
                print("value cr successfully set")
                return
            else:
                print("cr error:radio unable to set")
                return
        print("invalid cycling rate ")
        return

    def set_bw(self, bw):
        """set the bandwidth which can only be 125, 250 or 500 hz"""

        if bw in [125, 250, 500]:
            success = self.write_to_rn2483_radio(f"radio set bw {bw}")
            if success:
                print("value bw successfully set")
                return
            else:
                print("bw error: radio unable to set")
                return

        print("invalid receiving bandwidth")
        return

    def set_iqi(self, iqi):
        if iqi in ["on", "off"]:
            success = self.write_to_rn2483_radio("radio set iqi " + str(iqi))
            if success:
                print("value successfully set")
                return
            else:
                print("iqi error:radio unable to set")
                return

        print("invalid iqi setting")

    def set_sync(self, sync):

        # TODO: convert sync into hexadecimal
        # TODO: make sure sync is between 0- 255 for lora modulation
        # TODO: make sure sync is between 0 - 2^8 - 1 for fsk modulation

        success = self.write_to_rn2483_radio("radio set sync " + str(sync))
        if success:
            print("value sync word successfully set")
            return
        else:
            print("sync param error:radio unable to set ")
            return

    def set_prlen(self, pr):
        """set the preamble length between 0 and 65535"""

        if pr in range(0, 65535):
            success = self.write_to_rn2483_radio("radio set prlen " + str(pr))
            if success:
                print("preamble length successfully set")
                return
            else:
                print("error: unable to set preamble length ")
                return

        print("error: invalid preamble length")

    def set_crc(self, crc):
        """enable or disable the cyclic redundancy check"""

        if crc in ["on", "off"]:
            success = self.write_to_rn2483_radio("radio set crc " + str(crc))
            if success:
                print("value crc successfully set")
                return
            else:
                print("crc error:radio unable to set")
                return

        print("invalid crc param ")

    def set_rx_mode(self, message_q: queue.Queue):
        """set the rn2483 radio so that it constantly
           listens for transmissions"""

        # turn off watch dog timer
        self.write_to_rn2483_radio('radio set wdt 0')

        # this command must be passed before any reception can occur
        self.write_to_rn2483_radio("mac pause")

        # command radio to go into continuous reception mode
        success = self.write_to_rn2483_radio("radio rx 0")

        # if radio has not been put into rx mode
        if not success:
            print('error putting radio into rx mode')
            return

        # keep reading from serial port
        while True:
            message = str(self.ser.readline())

            if message != "b''":
                # trim unnecessary elements of the message
                message = message[10:-5]

                # put serial message in data queue for telemetry
                self.rn2483_radio_payloads.put(message)

                # put radio back into rx mode
                self.set_rx_mode(message_q)
            else:
                print('nothing received')

    def _tx(self, data):
        """transmit data, a method used for debugging

        ROCKET DOES NOT RESPOND TO TRANSMISSIONS AT THIS TIME"""

        # command that must be called before each transmission and receive
        self.write_to_rn2483_radio("mac pause")

        # is the data we wish to transmit valid?
        valid = self.write_to_rn2483_radio("radio tx " + data)

        if not valid:
            print('invalid transmission message')
            return

        else:
            i = 0

            # radio will send 'radio_tx_ok' when message has been transmitted
            while 'radio_tx_ok' not in str(self._read_ser()):

                # if message not transmitted then wait for 1/10th of a second
                time.sleep(0.1)

                i += 1

                # if we have waited 0.3 seconds, then stop waiting. something
                # has gone wrong.
                if i == 3:
                    print('unable to transmit message')
                    return

            print('successfully sent message')


def serial_ports() -> tuple[list[str], list[str]]:
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
    result = []
    for test_port in com_ports:
        try:
            s = Serial(test_port)
            s.close()
            result.append(test_port)
        except (OSError, SerialException):
            pass
    return com_ports, result
