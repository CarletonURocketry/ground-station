#
# Functions that are used to configure the ground station
#
import queue


def wait_for_ok(self):
    """
    Check to see if 'ok' is loaded onto the serial line by the ground station. If we receive 'ok' then this
    function returns True. If anything else is read form the serial line then this function returns False.
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


def set_mod(self, mod):
    if mod in ['lora', 'fsk']:
        success = self.write_to_ground_station('radio set mod ' + mod)

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

        success = self.write_to_ground_station("radio set pwr " + str(pwr))

        if success:
            print("value power successfully set")
            return

        else:
            print("power error:radio unable to set")
            return

    print("invalid power param")
    return


def set_sf(self, sf):
    """set the spreading factor for the ground station. Spreading factor
       can only be set to 7, 8, 9, 10, 11, or 12.

    """

    if sf in [7, 8, 9, 10, 11, 12]:
        success = self.write_to_ground_station("radio set sf sf" + str(sf))
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
        success = self.write_to_ground_station("radio set cr " + str(cr))
        if success:
            print("value cr successfully set")
            return
        else:
            print("cr error:radio unable to set")
            return
    print("invalid cycling rate ")
    return


def set_rxbw(self, bw):
    """set the bandwidth which can only  be 125, 250 or 500 hz"""

    if bw in [125, 250, 500]:
        success = self.write_to_ground_station("radio set bw " + str(bw))
        if success:
            print("value rxbw successfully set")
            return
        else:
            print("rxbw error:radio unable to set")
            return

    print("invalid receiving bandwidth  ")
    return


def set_iqi(self, iqi):
    if iqi in ["on", "off"]:
        success = self.write_to_ground_station("radio set iqi " + str(iqi))
        if success:
            print("value successfully set")
            return
        else:
            print("iqi error:radio unable to set")
            return

    print("invalid iqi setting ")


def set_sync(self, sync):
    # TODO: convert sync into hexadecimal
    # TODO: make sure sync is between 0- 255 for lora modulation
    # TODO: make sure sync is between 0 - 2^8 - 1 for fsk modulation

    success = self.write_to_ground_station("radio set sync " + str(sync))
    if success:
        print("value sync word successfully set")
        return
    else:
        print("sync param error:radio unable to set ")
        return


def set_prlen(self, pr):
    """set the preamble length between 0 and  65535"""

    if pr in range(0, 65535):
        success = self.write_to_ground_station("radio set prlen " + str(pr))
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
        success = self.write_to_ground_station("radio set crc " + str(crc))
        if success:
            print("value crc successfully set")
            return
        else:
            print("crc error:radio unable to set")
            return

    print("invalid crc param ")


def set_rx_mode(self, message_q: queue.Queue):
    """set the ground station so that it constantly
       listens for transmissions"""

    # turn off watch dog timer
    # self.write_to_ground_station('radio set wdt 0')

    # this command must be passed before any reception can occur
    self.write_to_ground_station("mac pause")

    # command radio to go into continuous reception mode
    success = self.write_to_ground_station("radio rx 0")

    # if radio has not been put into rx mode
    if not success:
        print('error putting radio into rx mode')
        return -1

    # keep reading from serial port
    while True:
        message = str(self.ser.readline())

        # if serial port has nothing that can be read
        if message == "b''":
            print('nothing received')

        else:
            # trim unnecessary elements of the message
            message = message[10:-5]
            message_q.put(message)
            print('message received:', message)
            # UI._parse_rx(message)

            # put radio back into rx mode
            self.set_rx_mode(message_q)
