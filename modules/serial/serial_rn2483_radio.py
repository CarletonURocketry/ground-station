# Serial communication to the RN2483 LoRa Radio Module
# Outputs radio payloads from the CU-InSpace rocket
#
# Authors:
# Arsalan Syed
# Thomas Selwyn (Devil)
# Zacchaeus Liang

import queue
import time
from multiprocessing import Queue, Process

from serial import Serial, SerialException, EIGHTBITS, PARITY_NONE


class SerialRN2483Radio(Process):

    def __init__(self, serial_status: Queue, rn2483_radio_input: Queue, rn2483_radio_payloads: Queue, serial_port: str):
        Process.__init__(self)

        self.serial_status = serial_status

        self.rn2483_radio_input = rn2483_radio_input
        self.rn2483_radio_payloads = rn2483_radio_payloads

        self.serial_port = serial_port
        self.ser = None

        self.run()

    def run(self):
        while True:
            try:
                # initiate the USB serial connection
                print(f"RN2483 Radio: Connecting to {self.serial_port}")
                # Settings matched to RN2483 Transceiver Data Sheet's default UART settings
                self.ser = Serial(port=self.serial_port,
                                  timeout=1,
                                  baudrate=57600,
                                  bytesize=EIGHTBITS,
                                  parity=PARITY_NONE,
                                  stopbits=1,
                                  rtscts=False)
                print(f"RN2483 Radio: Connected to {self.serial_port}")
                self.serial_connected.value = True
                self.serial_connected_port[0] = self.serial_port

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
                self.serial_connected.value = False
                self.serial_connected_port[0] = ""
                print("RN2483 Radio: Error communicating with serial device.")
                time.sleep(3)

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

        # set the transmission power state to 15. (15th TX Power state is 13.6dBm on the 433 MHz band)
        self.set_pwr(15)

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

        success = self.write_to_rn2483_radio(f"radio set freq {freq}")
        if success:
            print("frequency successfully set")
            return True
        else:
            print("error: frequency not set")
            return False

    def set_mod(self, mod):

        if mod in ['lora', 'fsk']:
            success = self.write_to_rn2483_radio(f"radio set mod {mod}")
            if success:
                print('successfully set modulation')
            else:
                print('error setting modulation')
        else:
            print('error setting modulation: either use fsk or lora')

    def set_pwr(self, pwr):
        """ set power state between -3 and 15. The 15th state has an output power of 14.1 dBm for the 868 MHz band
         and 13.6dBm for the 433 MHz band. """
        if pwr in range(-3, 16):
            success = self.write_to_rn2483_radio(f"radio set pwr {pwr}")
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
            success = self.write_to_rn2483_radio(f"radio set sf {sf}")
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
            success = self.write_to_rn2483_radio(f"radio set cr {cr}")
            if success:
                print("value cr successfully set")
                return
            else:
                print("cr error:radio unable to set")
                return
        print("invalid cycling rate")
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
            success = self.write_to_rn2483_radio(f"radio set iqi {iqi}")
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

        success = self.write_to_rn2483_radio(f"radio set sync {sync}")
        if success:
            print("value sync word successfully set")
            return
        else:
            print("sync param error:radio unable to set ")
            return

    def set_prlen(self, pr):
        """set the preamble length between 0 and 65535"""

        if pr in range(0, 65535):
            success = self.write_to_rn2483_radio(f"radio set prlen {pr}")
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
            success = self.write_to_rn2483_radio(f"radio set crc {crc}")
            if success:
                print("value crc successfully set")
                return
            else:
                print("crc error:radio unable to set")
                return

        print("invalid crc param ")

    def set_rx_mode(self):
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

    def check_for_transmissions(self):
        """checks for new transmissions on the line"""
        message = str(self.ser.readline())

        if message != "b''":
            # trim unnecessary elements of the message
            message = message[10:-5]

            # put serial message in data queue for telemetry
            self.rn2483_radio_payloads.put(message)

        else:
            print('nothing received')

    def _tx(self, data):
        """transmit data, a method used for debugging

        ROCKET DOES NOT RESPOND TO TRANSMISSIONS AT THIS TIME"""

        # command that must be called before each transmission and receive
        self.write_to_rn2483_radio("mac pause")

        # is the data we wish to transmit valid?
        valid = self.write_to_rn2483_radio(f"radio tx {data}")

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
