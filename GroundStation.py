# Ground station software for communication with the CU-InSpace rocket via an
# RN2483 LoRa radio module.
# Authors: 
# 


import serial
import queue
import packets
import time
import struct
import data_block
import os

class GroundStation:
    
    def __init__(self, com_port='COM4'):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(curr_dir, 'data_log.txt')
        self.log = open(log_path, 'w')


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

    def _read_ser(self):
        # read from serial line
        rv = str(self.ser.readline())

        return rv

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

        print('successfully set GPIO')

    def reset(self):
        """perform a software reset on the ground station"""

        self.write_to_ground_station('sys reset')

        # confirm from the ground station that the reset was a success
        ret = self._read_ser()

        if 'RN2483' in ret:
            print('radio successfully reset')
            return True
        else:
            return False

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
        self.reset()
        
        # initilize all the pins to be inputs
        self.init_gpio()
        
        # set modulation type to lora
        self.set_mod('lora')
    
        # set the frequency of the radio (Hz)
        self.set_freq(433050000)
        
        # set the transmission power to 15 db (max POWARRRR)
        self.set_pwr(14)
        
        # set the transmission spreading factor. The higher the spreading factor,
        # the slower the transmissions (symbols are spread out more) and the better
        # the reception and error prone the system is.
        self.set_sf(9)
        
        # set the coding rate (ratio of actual data to error-correcting data that
        # is transmitted. The lower the coding rate the lower the data rate.
        self.set_cr("4/7")
        
        # set reception bandwidth. This should match the transmission bandwidth of the 
        # node that this ground station is trying to recieve.
        #self.set_rxbw(500)
        
        # set the length of the preamble. Preamble means introduction. It's a 
        # transmission that is used to synchronize the reciever.
        self.set_prlen(6)
        
        # set cyclic redundancy check on/off. This is used to detect errors
        # in the recieved signal
        self.set_crc("on")
        
        # set the invert IQ function
        self.set_iqi("off")
        
        # set sync word to be 0x43
        self.set_sync("43")

        # set the bandwidth of reception
        self.set_bw(500)

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
        
        # must include carriage return for valid commands (see DS40001784B pg XX)
        data = data + "\r\n"
        
        # encode command_string as bytes and then transmit over serial port
        self.ser.write(data.encode('utf-8'))  
        
        # wait for response on the serial line. Return if 'ok' received
        # sys reset gives us info about the board which we want to process differently from other commands
        if command_string != 'sys reset' and command_string != 'radio get snr' and command_string != 'radio get rssi':
            #TODO: clean this up with read functions
            return self.wait_for_ok()

    def process_response(self, response:str) -> str:
        """
        Removes the carriage return from the output received 
        from the radio.
        Author: Fahim
        @param  response: contains response from radio
        @return: the response received from radio in a clean format. 
        will return -1 if error is found.
        >>strip_output("b'21313123321\r\n'")
        21313123321
        """
        # if we don't get a response
        if len(response) == 0:
            return -1
        if response == '\r\n':
            return -1 
        
        # remove carriage return value
        return response.decode('UTF-8')[:-2]

    def load_map(self):
        """load in a map that can be used offline
            author: """

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

    def set_freq(self, freq):
        """set the frequency of transmitted signals"""

        if not((freq >= 433050000 and freq <= 434790000) or (freq >= 863000000 and freq <= 870000000)):
            print('invalid frequency parameter.')
            return False

        success = self.write_to_ground_station("radio set freq " + str(freq))
        
        if success:
            print("frequency successfully set")
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

    def set_pwr(self, pwr):
        """ set power possible values between -3 and 14 db"""
        #TODO: FIGURE OUT MAX POWER
        if pwr in range(-3, 16):
            
            success =  self.write_to_ground_station("radio set pwr " + str(pwr))
            
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
            sucess = self.write_to_ground_station("radio set sf sf" + str(sf))
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

    def set_rxbw(self, bw):
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

    def set_iqi(self, iqi):
        if iqi in ["on", "off"]:
            sucess= self.write_to_ground_station("radio set iqi " + str(iqi))
            if sucess:
                print("value sucessfully set")
                return
            else:
                print("iqi error:radio unable to set")
                return
            
        print("invalid iqi setting ")

    def set_sync(self, sync):
        
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

    def set_prlen(self, pr):
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

    def set_crc(self, crc):
        """enable or disable the cyclic redundancy check"""
        
        if crc in ["on", "off"]:
            success = self.write_to_ground_station("radio set crc " + str(crc))
            if success:
                print("value crc sucessfully set")
                return
            else:
                print("crc error:radio unable to set")
                return
            
        print("invalid crc param ")


    def set_bw(self, bw):
        #TODO finish this function
        self.write_to_ground_station('radio set bw {}'.format(str(bw)))

    def parse_rx(self, data):

        try:
            packet = bytes.fromhex(data)
        except:
            print('error: data is {}'.format(data))
            return

        call_sign = packet[0:6]

        # remove packet header from rest of data
        packet = packet[12:]

        while len(packet) != 0:

            block_header = struct.unpack('<I', packet[0:4])

            length = ((block_header[0] & 0x1f)) * 4
            signed = ((block_header[0] >> 5) & 0x1)
            _type = ((block_header[0] >> 6) & 0xf)
            subtype = ((block_header[0] >> 10) & 0x3f)
            dest_addr = ((block_header[0] >> 16) & 0xf)

            if _type == 0 and subtype == 0:
                # this is a signal report
                self.write_to_ground_station('radio get snr')
                snr = self._read_ser()

                self.write_to_ground_station('radio get rssi')
                rssi = self._read_ser()

                print('-------------------------------------------------------------------------------------------------------')
                print('{} has asked for a signal report\n'.format(call_sign))
                print('the SNR is {} and the RSSI is {}'.format(snr, rssi))
                print('-------------------------------------------------------------------------------------------------------')

                logging_info = 'signal report at {}. SNR is {}, RSSI is {}\n'.format(time.time(), snr, rssi)
                self.log.write(logging_info)

            else:
                payload = packet[4:4 + length]
                try:
                    block = data_block.DataBlock.from_payload(subtype, payload)
                    print('-------------------------------------------------------------------------------------------------------')
                    print('{} sent you a packet:\n'.format(str(call_sign)))
                    print(block)
                    print( '-------------------------------------------------------------------------------------------------------')
                    logging_info = '{}\n'.format(block)
                    self.log.write(logging_info)

                except:
                    print('could not parse incoming packet of type {}, subtype: {}\n'.format(_type, subtype))

            # move to next block
            packet = packet[length + 4:]

        self.log.flush()
        os.fsync(self.log.fileno())


    def set_rx_mode(self, message_q:queue.Queue):
        """set the ground station so that it constantly
           listens for transmissions"""
        
        # turn off watch dog timer
        self.write_to_ground_station('radio set wdt 0')
        
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
                # trim unecessary elements of the message
                message = message[10:-5]

                self.parse_rx(message)

                # put radio back into rx mode
                self.set_rx_mode(message_q)
            
    def _tx(self, data):
        """transmit data, a method used for debugging"""
        
        # command that must be called before each transmission and recieve
        self.write_to_ground_station("mac pause")
        
        # is the data we wish to transmit valid?
        valid = self.write_to_ground_station("radio tx " + data)

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





    # header = bytes.fromhex('840C0000')
    # header = struct.unpack('<I', header)
    #
    # length = ((header[0] & 0x1f) + 1) * 4
    # signed = ((header[0] >> 5) & 0x1)
    # _type = ((header[0] >> 6) & 0xf)
    # subtype = ((header[0] >> 10) & 0x3f)
    # dest_addr = ((header[0] >> 16) & 0xf)
    #
    # ## abstract class
    # payload = bytes.fromhex("E01F00008D540100BC57000010FEFFFF")
    # block = DataBlock.from_payload(subtype, payload)
    # print(block)

    # signal report
    # get snr over time and log it.


# the COM port that is being used.
tx = GroundStation('COM8')

# initialize the ground station
tx.init_ground_station()

print('_____________________________________')
q = queue.Queue()
tx.set_rx_mode(q)
