# Ground station software for communication with the CU-InSpace rocket via an
# RN2483 LoRa radio module.
# Authors:


import serial

ser = serial.Serial( port = "COM4",
                         timeout=1,
                         baudrate=57600,
                         # number of bits per message
                         bytesize=serial.EIGHTBITS,
                         # set parity check: no parity
                         parity=serial.PARITY_NONE,
                         # number of stop bits
                         stopbits = 1, 
                         # disable hardware (RTS/CTS) flow control 
                         rtscts=False)   

def init_serial(port):
    
        
    return 0
    


def init_GPIO():
    write_to_ground_station("sys set pinmode GPIO0 digin")
    write_to_ground_station("sys set pinmode GPIO1 digin")
    write_to_ground_station("sys set pinmode GPIO2 digin")
    write_to_ground_station("sys set pinmode GPIO3 digin")
    write_to_ground_station("sys set pinmode GPIO4 digin")
    write_to_ground_station("sys set pinmode GPIO5 digin")
    write_to_ground_station("sys set pinmode GPIO6 digin")
    write_to_ground_station("sys set pinmode GPIO7 digin")
    write_to_ground_station("sys set pinmode GPIO8 digin")
    write_to_ground_station("sys set pinmode GPIO9 digin")
    write_to_ground_station("sys set pinmode GPIO10 digin")
    write_to_ground_station("sys set pinmode GPIO11 digin")
    write_to_ground_station("sys set pinmode GPIO12 digin")
    write_to_ground_station("sys set pinmode GPIO13 digin")    

def init_ground_station():
    
    # initlize a serial port
    init_serial("COM4")

    # initlize all the pins to be inputs
    init_GPIO()

   # set the frequency of the radio
    radio_set_freq(433050000)
    
    # set the power to -14 db
    radio_set_pwr(-3)
    
    # set the spreading factor
    radio_set_sf("sf9")
    
    # set the coding rate
    radio_set_cr("4/7")
    
    # set bandwdith
    radio_set_rxbw(500)
    
    # set prlen preamble length
    radio_set_prlen(6)
    
    # set crc
    radio_set_crc("on")
    
    # set iqi
    radio_set_iqi("on")
    
    # set sync word to be 0x43
    radio_set_sync("43")
    
    print("sucessfully configured lora radio")


    
def write_to_ground_station(command_string): 
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
    
    #must include carriage return for valid commands (see DS40001784B pg XX)
    data = data + "\r\n"
    
    # encode command_string as bytes and then transmit over serial port
    ser.write(data.encode('utf-8'))  
    
    #if ground station produces error in response to command then it will 
    #halt the program 
    return wait_for_ok()
    
   


def read_from_ground_station(register: int):
    """reads data from the ground station via UART and puts it into the 
       correct data format to be passed onto the UI (check the logging format)
       author: elias 
       @param  register: address of register to read from
       @return data: the data that is stored in that register
    """


def load_map():
    """load in a map that can be used offline
        author: """

# wait for serial response we have set a timeout value so it will wait for a response and checks if it's not ok

def wait_for_ok():
   # flush the serial port
    ser.flush()
    
    #read 'ok' from the terminal, if it's there. 
    rv = str(ser.readline())
    
    if ('ok' in rv):  # check for ok and report if param invalid
        return True
    
    elif rv != 'ok':
        print("ERROR: wait_for_ok(): " + rv)
        return False



def radio_set_freq(freq):
    
    #frequencies = [250000, 125000, 62500.0, 31300.0, 15600.0, 7800.0, 3900.0,
     #              200000, 100000, 50000, 25000, 12500.0, 6300.0, 3100.0, 
      #             166700.0, 83300.0, 41700.0, 20800.0, 10400.0, 5200.0, 2600.0]
    #if freq in frequencies:
    
    success = write_to_ground_station("radio set freq " + str(freq))
    if(success):
        print("frequency sucessfully set")
        return True
    else:
        print("error: frequency not set")
        return False
            

# set power possible values between -3 and 14 db
def radio_set_pwr(pwr):
    if pwr in range(-3, 14):
        sucess=  write_to_ground_station("radio set pwr " + str(pwr))
        if sucess:
            print("radio_set_pwr(): value power sucessfully set")
        else:
            print("radio_set_pwr(): power error:radio unable to set")
            print("radio_set_pwr(): invalid power param ")



def radio_set_sf(sf):
    if sf in ["sf7", "sf8", "sf9", "sf10", "sf11", "sf12"]:
        sucess= write_to_ground_station("radio set sf " + sf)
        if sucess:
            print("value spreading factor sucessfully set")
        else:
            print("spreading factor  error:radio unable to set")
            print("invalid spreading factor error")
# set coding rate which can only be "4/5", "4/6", "4/7", "4/8"


def radio_set_cr(cr):
    if cr in ["4/5", "4/6", "4/7", "4/8"]:
        sucess= write_to_ground_station("radio set cr " + str(cr))
        if sucess:
            print("value cr sucessfully set")
        else:
            print("cr error:radio unable to set")
            print("invalid cycling rate ")

# set the bandwidth which can only  be 125 250 or 500 hz


def radio_set_rxbw(bw):
    if bw in [125, 250, 500]:
        sucess= write_to_ground_station("radio set bw " + str(bw))
        if sucess:
            print("value rxbw sucessfully set")
        else:
            print("rxbw error:radio unable to set")
            print("invalid recieving bandwidth  ")

# set IQI to be on or off


def radio_set_iqi(iqi):
    if iqi in ["on", "off"]:
        sucess= write_to_ground_station("radio set iqi " + str(iqi))
        if sucess:
            print("value sucessfully set")
        else:
            print("iqi error:radio unable to set")
            print("invalid iqi setting ")
# set sync word it's a 2 bytes no error checking is done because it's confusing to change between types


def radio_set_sync(sync):
    sucess= write_to_ground_station("radio set sync " + str(sync))
    if sucess:
        print("value sync word sucessfully set")
    else:
        print("sync param error:radio unable to set ")


# set the preamble length between 0 and  65535
def radio_set_prlen(pr):
    if pr in range(0, 65535):
        sucess=write_to_ground_station("radio set prlen " + str(pr))
        if sucess:
            print("value prlen sucessfully set")
        else:
            print("prlen error:radio unable to set ")
            print("invalid preamble length")

# crc can only be set to True or false to enable error checking


def radio_set_crc(crc):
    if crc in ["on", "off"]:
        sucess= write_to_ground_station("radio set crc " + str(crc))
        if sucess:
            print("value crc sucessfully set")
        else:
            print("crc error:radio unable to set")
            print("invalid crc param ")


def radio_set_rxmode():
    # set the timeout to 65535 the maximum amount
    # we will set this value to be the transmission 
    #The mac pause command must be called before any radio transmission
    #or reception, even if no MAC operations have been initiated before.

    write_to_ground_station(str("mac pause", "utf-8"))

    # set rx amount to the amount of bytes we need 
    #suggestion is to keep it to 0 since we know the packet lenght and anoumt of blocks is varible 
    write_to_ground_station(str("radio rx 0", "utf-8"))
def test_radio():
    #send a valid command which get's frequency

    while(1):
        write_to_ground_station(str("radio get freq "+ "\r\n", "utf-8"))
        rv = ser.readline()
        print(rv)
def radio_set_txmode(data):
    write_to_ground_station(str("radio tx "+data+"\r\n", utf8))   
 
 

 #comment out beyond this point to debug the serial commnications 
class signal_report:
    signal_noise_ratio=0
    recieved_signal_strength=0
    TX_power=0
    
    def set_signal_ratio(bits):
        snr_bits=bits[0:7]
        value=bytearray(snr_bits)
        signal_noise_ratio=value.int 
    def set_rssi(bits):
        rssi_bits=bits[8:15]
        value=bytearray(rssi_bits)
        recieved_signal_strength=value.int
        
    def set_tx_power(data):
        rssi_bits=bits[8:15]
        value=bytearray(rssi_bits)
        value=value.int
        
        
#order is wrong correct when pushing TODO 
class altitude:
      time = 0
      pressure = 0
      temp = 0
      altitude = 0
      
      def set_time(bits):
          time_bits=bits[0:31]
          time_bits=BitArray(bits)
          time=a.int
          
      def set_pressure(bits):
          pressure_bits = bits[32:63]
          presure_bits = BitArray(bits)
          pressure=pressure_bits.int
          
      def set_temp(bits):
          temp_bits = bits[64:94]
          temp_bits = BitArray(bits)
          temp=temp.int
          
      def set_altitude(bits): 
           altitude_bits = bits[32:62]
           altitude_bits = BitArray(bits)
           altitude=altitude_bits.int

class acceleration: 
    time = 0
    fsr = 0 
    x_axis = 0
    y_axis = 0
    z_axis = 0
    
    def set_time(bits):
        time_bits = bits[32:62]
        time_bits = BitArray(time_bits)
        time=time.uint # parse as unsigned? 
    def set_fsr(bits):
        fsr_bits=bits[32:39]
        fsr_bits=BitArray(fsr_bits)
        fsr=fsr_bits.int# unsigned? 
    def set_x_axis(bits):
        xa_bits = bits[]

    

        

