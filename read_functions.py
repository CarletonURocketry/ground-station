# radio commands
def read_frequency(self):
    freq = int(self.read_from_ground_station("freq"))
    UPPER_1 = 434800000
    LOWER_1 = 433000000
    UPPER_2 = 870000000
    LOWER_2 = 863000000

    if (freq > LOWER_1 and freq < UPPER_1):
        return freq
    elif (freq > LOWER_2 and freq < UPPER_2):
        return freq
    else:
        return -1


def read_bitrate(self):
    bitrate = int(strip_output(read_from_ground_station("bitrate")))
    UPPER_1 = 65535
    LOWER_1 = 0
    if (bitrate > LOWER_1 and bitrate < UPPER_1):
        return bitrate
    else:
        return -1


def read_bw(self):
    bw = int(strip_output(read_from_ground_station("bw")))
    possibilities = [125, 250, 500]  # the three possible values
    if (bw in possibilities):
        return bw
    else:
        return -1


def read_cr(self):
    cr = self.read_from_ground_station("cr")

    possibilities = ['4/5', '4/6', '4/7', '4/8']  # the four possible strings
    if (cr in possibilities):
        return cr
    else:
        return -1


def read_bt(elf):
    bt = strip_output(read_from_ground_station("bt"))
    possibilities = ['none', '1.0', '0.5', '0.3']  # the four possible strings
    if (bt in possibilities):
        return bt
    else:
        return -1


def read_crc(self):
    return read_from_ground_station("crc")


def read_fdev(elf):
    return read_from_ground_station("fdev")


def read_afcbw(self):
    return read_from_ground_station("afcbw")


def read_iqi(self):
    return read_from_ground_station("iqi")


def read_mod(self):
    return self.read_from_ground_station("mod")


def read_prlen(self):
    return read_from_ground_station("prlen")


def read_pwr(self):
    return read_from_ground_station("pwr")


def read_rssi(self):
    return read_from_ground_station("rssi")


def read_rxbw(self):
    return read_from_ground_station("rxbw")


def read_sf(self):
    return read_from_ground_station("sf")


def read_snr(self):
    return read_from_ground_station("snr")


def read_sync(self):
    return read_from_ground_station("sync")


def read_wdt(self):
    return read_from_ground_station("wdt")


# sys commands
def read_ver(self):
    return read_from_ground_station("ver")


def read_vdd(self):
    return read_from_ground_station("vdd")


def read_hweui(self):  # remove?
    return read_from_ground_station("hweui")


def read_nvm(address: str):
    """
    Accepts hexadecimal address from 300 to 3FF.
    """
    return read_from_ground_station("nvm " + address)


def read_pindig(self, pinName: str):  # remove
    """
    Accepts GPIO0 - 13, UART_CTS, UART_RTS, TEST0-1.
    """
    return read_from_ground_station("pindig " + pinName)


def read_pinana(self, pinName: str):  # remove
    """
    Accepts GPIO0 - 3, and GPIO5 - 13
    Enter only the pin #, as GPIO is already accounted for
    """
    return read_from_ground_station("pinana GPIO" + pinName)


def read_from_ground_station(self, command: str):
    """reads data from the ground station via UART
   author: Fahim

   @param  command: contains commmand that will be written to ground station
   @return: the message received from station
            will return -1 if error is found
    """
    command = str(command)

    # split command into individual words if command is more than one word
    # long. Example:  'nvm 300'
    cmds = command.split()

    # these are parameters that require a 'sys' call. Ex. 'sys get vdd'
    sys_commands = ['vdd', 'nvm', 'ver', 'hweui', 'pindig', 'pinana']

    if (cmds[0] in sys_commands):
        self.write_to_ground_station("sys get " + command)

    # if parameter to be read is not covered by 'sys', it requires 'radio'
    else:
        self.write_to_ground_station("radio get " + command)

    # if command was recieved and valid:
    return self.process_response(self.ser.readline())

