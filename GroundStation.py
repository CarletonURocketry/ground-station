# Ground station software for communication with the CU-InSpace rocket via an
# RN2483 LoRa radio module.
# Authors: 
# 


import serial
import queue

class GroundStation:
    
    def __init__(self, com_port='COM4'):
        
        # initiate the USB serial connection
        self.ser = serial.Serial(port=com_port,
                                 timeout=1,
                                 baudrate=57600,
                                 # number of bits per message
                                 bytesize=serial.EIGHTBITS,
                                 # set parity check: no parity
                                 parity=serial.PARITY_NONE,
                                 # number of stop bits
                                 stopbits=1,
                                 # disable hardware (RTS/CTS) flow control
                                 rtscts=False)

    def init_gpio(self):
        """set all GPIO pins to input mode, thereby putting them in a state of high impedence"""
        
        self.write_to_ground_station("sys set pinmode GPIO0 digin")
        self.write_to_ground_station("sys set pinmode GPIO1 digin")
        self.write_to_ground_station("sys set pinmode GPIO2 digin")
        self.write_to_ground_station("sys set pinmode GPIO3 digin")
        self.write_to_ground_station("sys set pinmode GPIO4 digin")
        self.write_to_ground_station("sys set pinmode GPIO5 digin")
        self.write_to_ground_station("sys set pinmode GPIO6 digin")
        self.write_to_ground_station("sys set pinmode GPIO5 digin")
        self.write_to_ground_station("sys set pinmode GPIO6 digin")
        self.write_to_ground_station("sys set pinmode GPIO7 digin")
        self.write_to_ground_station("sys set pinmode GPIO8 digin")
        self.write_to_ground_station("sys set pinmode GPIO9 digin")
        self.write_to_ground_station("sys set pinmode GPIO10 digin")
        self.write_to_ground_station("sys set pinmode GPIO11 digin")
        self.write_to_ground_station("sys set pinmode GPIO12 digin")
        self.write_to_ground_station("sys set pinmode GPIO13 digin")    

    def init_ground_station(self):
        """initialize the ground station with default parameters for the following parameters:
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
        self.write_to_ground_station('sys reset')
        
        # initlize all the pins to be inputs
        self.init_gpio()
        
        # set modulation type to lora
        self.set_mod('lora')
    
        #set the frequency of the radio (433 MHz)
        self.set_freq(433000000)
        
        # set the transmission power to 15 db (max POWARRRR)
        self.set_pwr(15)
        
        # set the transmission spreading factor. The higher the spreading factor,
        # the slower the transmissions (symbols are spread out more) and the better
        # the reception and error prone the system is.
        self.set_sf(11)
        
        # set the coding rate (ratio of actual data to error-correcting data that
        # is transmitted. The lower the coding rate the lower the data rate.
        self.radio_set_cr("4/7")
        
        # set reception bandwidth. This should match the transmission bandwidth of the 
        # node that this ground station is trying to recieve.
        self.radio_set_rxbw(500)
        
        # set the length of the preamble. Preamble means introduction. It's a 
        # transmission that is used to synchronize the reciever.
        self.radio_set_prlen(8)
        
        # set cyclic redundancy check on/off. This is used to detect errors
        # in the recieved signal
        self.radio_set_crc("off")
        
        # set the invert IQ function
        #self.radio_set_iqi("on")
        
        # set sync word to be 0x43
        #self.radio_set_sync("43")
        


    def read_ser(self):
        rv = str(self.ser.readline())
        
        return rv
    
    def write_to_ground_station(self, command_string):
        """writes data to the ground station via UART
        author: Tarik
        @param command_string: full command to be send to the ground station
        @param COM_PORT: the COM port to be used for the UART transmission
        
        Ex.
        >>write_to_ground_station("radio set pwr 7", COM1)
        >>"ok"
        
        //above example sets the radio tramission power to 7 using COM1
        
        """

        data = str(command_string)
        
        # flush the serial port
        self.ser.flush()        
        
        #must include carriage return for valid commands (see DS40001784B pg XX)
        data = data + "\r\n"
        
        # encode command_string as bytes and then transmit over serial port
        self.ser.write(data.encode('utf-8'))  
        
        # wait for response on the serial line. Return if 'ok' recieved 
        return self.wait_for_ok()
    

    def process_response(self, response:str) -> str:
        """
        Removes the carriage return from the output received 
        from the radio.
        Author: Fahim
        @param  response: contains response from radio
        @return: the response received from radio in a clean format. 
        will return -1 if error is found.
        >>>strip_output("b'21313123321\r\n'")
        21313123321
        """
        #if we don't get a response
        if len(response) == 0:
            return -1
        if response == '\r\n':
            return -1 
        
        #remove carriage return value 
        return response.decode('UTF-8')[:-2]
    
    
    #radio commands
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
        possibilities = [125,250,500] #the three possible values
        if (bw in possibilities):
            return bw
        else:
            return -1
    
    def read_cr(self):
        cr = self.read_from_ground_station("cr")
        
        possibilities = ['4/5','4/6','4/7','4/8'] #the four possible strings 
        if (cr in possibilities):
            return cr
        else:
            return -1
    
    def read_bt(elf):
        bt = strip_output(read_from_ground_station("bt"))
        possibilities = ['none','1.0','0.5','0.3'] #the four possible strings
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
    
    #sys commands
    def read_ver(self):
        return read_from_ground_station("ver")
    
    def read_vdd(self):
        return read_from_ground_station("vdd")
    
    def read_hweui(self): #remove?
        return read_from_ground_station("hweui")
    
    def read_nvm(address: str):
        """
        Accepts hexadecimal address from 300 to 3FF.
        """
        return read_from_ground_station("nvm " + address)
    
    def read_pindig(self, pinName: str): #remove
        """
        Accepts GPIO0 - 13, UART_CTS, UART_RTS, TEST0-1.
        """
        return read_from_ground_station("pindig " + pinName)
    
    def read_pinana(self, pinName: str): #remove
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
        
        #split command into individual words if command is more than one word
        #long. Example:  'nvm 300'
        cmds = command.split()
        
        #these are parameters that require a 'sys' call. Ex. 'sys get vdd'
        sys_commands = ['vdd', 'nvm','ver','hweui','pindig','pinana']
        
        if(cmds[0] in sys_commands): 
            self.write_to_ground_station("sys get " + command)
        
        #if parameter to be read is not covered by 'sys', it requires 'radio'
        else:
            self.write_to_ground_station("radio get " + command)
    
        #if command was recieved and valid:
        return self.process_response(self.ser.readline())

        
    def load_map(self):
        """load in a map that can be used offline
            author: """

    
    def wait_for_ok(self):
        """ 
        wait for serial response.
        """
        
        #read 'ok' from the terminal, if it's there.
        rv = str(self.ser.readline())
        
        if ('ok' in rv):  # check for ok and report if param invalid
            return True
        
        elif rv != 'ok':
            # returned after mac pause command
            if '4294967245' in rv:
                return True
            
            print('wait for ok: ' + rv)
            
            return False


    def radio_set_freq(self, freq):
        """set the frequency of transmitted signals"""
        
        success = self.write_to_ground_station("radio set freq " + str(freq))
        
        if(success):
            print("frequency sucessfully set")
            return True
        else:
            print("error: frequency not set")
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
            
    
    def radio_set_pwr(self, pwr):
        """ set power possible values between -3 and 14 db"""
        
        if pwr in range(-3, 15):
            
            sucess=  self.write_to_ground_station("radio set pwr " + str(pwr))
            
            if sucess:
                print("value power sucessfully set")
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
            sucess = self.write_to_ground_station("radio set sf sf" + sf)
            if sucess:
                print("value spreading factor sucessfully set")
                return
            else:
                print("ERROR: unable to set spreading factor")
                return
                
        print("ERROR: invalid spreading factor")
        return


    def set_cr(self, cr):
        """set coding rate which can only be "4/5", "4/6", "4/7", "4/8"""
        
        if cr in ["4/5", "4/6", "4/7", "4/8"]:
            sucess=self.write_to_ground_station("radio set cr " + str(cr))
            if sucess:
                print("value cr sucessfully set")
                return
            else:
                print("cr error:radio unable to set")
                return
        print("invalid cycling rate ")
        return

    def radio_set_rxbw(self, bw):
        """set the bandwidth which can only  be 125, 250 or 500 hz"""
        
        if bw in [125, 250, 500]:
            sucess= self.write_to_ground_station("radio set bw " + str(bw))
            if sucess:
                print("value rxbw sucessfully set")
                return
            else:
                print("rxbw error:radio unable to set")
                return
            
        print("invalid recieving bandwidth  ")
        return


    def radio_set_iqi(self, iqi):
        if iqi in ["on", "off"]:
            sucess= self.write_to_ground_station("radio set iqi " + str(iqi))
            if sucess:
                print("value sucessfully set")
                return
            else:
                print("iqi error:radio unable to set")
                return
            
        print("invalid iqi setting ")
        

    def radio_set_sync(self, sync):
        
        #TODO: convert sync into hexademical
        #TODO: make sure sync is between 0- 255 for lora modulation
        #TODO: make sure sync is between 0 - 2^8 - 1 for fsk modulation
        
        sucess= self.write_to_ground_station("radio set sync " + str(sync))
        if sucess:
            print("value sync word sucessfully set")
            return
        else:
            print("sync param error:radio unable to set ")
            return


    def radio_set_prlen(self, pr):
        """set the preamble length between 0 and  65535"""
        
        if pr in range(0, 65535):
            sucess=self.write_to_ground_station("radio set prlen " + str(pr))
            if sucess:
                print("preamble length sucessfully set")
                return
            else:
                print("error: unable to set preamble length ")
                return 
            
        print("error: invalid preamble length")


    def radio_set_crc(self, crc):
        """enable or disable the cyclic redundancy check"""
        
        if crc in ["on", "off"]:
            sucess= self.write_to_ground_station("radio set crc " + str(crc))
            if sucess:
                print("value crc sucessfully set")
                return
            else:
                print("crc error:radio unable to set")
                return
            
        print("invalid crc param ")

    
    def _parse_packet_header(self, header):
        pass
    
    
    def _parse_block_header(self, header):
        
        # convert into binary 
        header = binary(header)
        
        # length of block in bytes (including header)
        block_len = header[0:5]
        
        # the number of chars needed to represent the block_len value
        # ex. 0b'10 == 0xA --> num chars needed to represent this == 1 
        block_len_hex = (block_len // 16) + 1 
        
        # does the message have a cryptographic signiture?
        sig = header[5]
        if sig == 1: 
            sig = True
        else:
            sig = False
        
        subtype = header[10:16]
        if subtype == 3:
            subtype = 'altitude_data'
        elif subtype == 4:
            subtype = 'acceleration'
        elif subtype == 5:
            subtype = 'angular_velocity_data'
        elif subtype == 6:
            subtype = 'GNSS_location_data'
        elif subtype == 7:
            subtype = 'GNSS_metadata'
        elif subtype == 8:
            subtype = 'power_information'
        elif subtype == 9:
            subtype = 'temperatures'
        elif subtype == 'A':
            subtype = 'MPU9250_IMU_data_data'
        elif subtype == 'B':
            subtype = 'KX134-1211_accelerometer_data'
        else:
            subtype = -1 
            
            
        dest_addr = header[16:20]
        
    
    
    def parse_rx(data):
        
        # extract the packet header 
        call_sign, length, version, srs_addr, packet_num = parse_packet_header(data[:24])
        
        # if this packet nothing more than just the packet header
        if length < 24:
            q.put(None)
            return
        
        # remove the packet header
        blocks = data[24:]
        
        while blocks != '':
            block_header = blocks[:8]
            
            data_len, sig, _type, _subtype, dest_addr = self.parse_block_header(block_header)
            
            
            data = blocks[8: 8 + data_len]
            
            if _type == 'altitude_data':
                data = altitude(data)
            
            elif _type == 'acceleration_data':
                pass
            
            elif _type == 'angular_velocity_data':
                pass
            
            elif _type == 'GNSS_location_data':
                pass
            
            elif _type == 'GNSS_metadata_data':
                pass
            
            elif _type == 'MPU9250_IMU_data_data':
                pass
            
            elif _type == 'KX134-1211_accelerometer_data':
                pass
            
            else:
                q.add(-1)
                return
            
            # remove the data we processed from the whole
            blocks = blocks[8 + data_len: ]
            
            q.add(data)

    def set_rx_mode(self):
        """set the ground station so that it constantly
           listens for transmissions"""
        
        # turn off watch dog timer
        self.write_to_ground_station('radio set wdt 0')
        
        # this command must be passed before any reception can occur 
        self.write_to_ground_station("mac pause")

        # command radio to go into continous reception mode 
        command_recieved = self.write_to_ground_station("radio rx 0")
        
        # if radio recieved command from computer
        return command_recieved
        
            
    def _tx(self, data):
        """transmit data, a method used for debugging"""
        
        # command that must be called before each transmission and recieve
        self.write_to_ground_station("mac pause")
        
        # is the data we wish to transmit valid?
        valid = self.write_to_ground_station("radio tx " + data )
        
        if not valid:
            print('invalid transmission message')
            return 
        
        else:
            i = 0
            
            # radio will send 'radio_tx_ok' when message has been transmitted
            while 'radio_tx_ok' not in str(self.read_ser()):
                
                # if message not transmitted then wait for 1/10th of a second
                time.sleep(0.1)
                
                i += 1
                
                # if we have waited 0.3 seconds, then stop waiting. something 
                # has gone wrong. 
                if i == 3:
                    print('unable to transmit message')
                    return 
                
            print('successfully sent mesage')
            

# for debugging     

import time
import threading

tx = GroundStation()
rx = GroundStation('COM7')

rx.init_ground_station()
tx.init_ground_station()

#rx.write_to_ground_station('radio rx 0')
#tx.write_to_ground_station('radio rx 1')

#rx.radio_set_rxmode()
rx.write_to_ground_station('mac pause')
rx.write_to_ground_station('radio rx 0')

tx.write_to_ground_station('mac pause')
tx.write_to_ground_station('radio set pwr 10')
tx.write_to_ground_station('radio tx 1234562')




print('_____________________________________')

#t = threading.Thread(target=__tx, args=(tx,))F
#t.start()
#r = threading.Thread(target=__rx, args=(rx,))
#r.start()

while True:
    rx.write_to_ground_station('mac pause')
    rx.write_to_ground_station('radio rx 0')    
    tx._tx('1000')
    time.sleep(1)
    #rx._tx('1000')
    print('rx:', rx.wait_for_ok())