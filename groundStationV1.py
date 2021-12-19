# Ground station software for communication with the CU-InSpace rocket via an
# RN2483 LoRa radio module.
# Authors:


import serial
from bitstring import BitArray
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
    radio_set_pwr(14)
    
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
        print("ERROR: wait for ok(): " + rv)
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
            print("value power sucessfully set")
        else:
            print("power error:radio unable to set")
    print("invalid power  param ")
# set spreading factor can only be set to  sf7", "sf8", "sf9", "sf10", "sf11", "sf12"]


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
        sucess=xwrite_to_ground_station("radio set cr " + str(cr))
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
    sucess= write_to_ground_station("radio set sync" + str(sync))
    if sucess:
        print("value sync word sucessfully set")
    else:
        print("sync param error:radio unable to set ")


# set the preamble length between 0 and  65535
def radio_set_prlen(pr):
    if pr in range(0, 65535):
        sucess=write_to_ground_station("radio set pr" + str(pr))
        if sucess:
            print("value prlen sucessfully set")
        else:
            print("prlen error:radio unable to set ")
    print("invalid preamble length")

# crc can only be set to True or false to enable error checking


def radio_set_crc(crc):
    if crc in ["on", "off"]:
        sucess= write_to_ground_station("radio set crc" + str(crc))
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
 
#  #comment out beyond this point to debug the serial commnications


class altitude:
     
      def __init__(self, bits):
          set_time(self,bits)
          set_pressure(self,bits)
          set_temp(self,bits)
          set_altitude(self,bits)
      def set_time(self,bits):
          time_bits=bits[0:32]
          time_bits=BitArray(bits)
          self.time=time.int
      def set_pressure(self,bits):
          pressure_bits = bits[32:64]
          presure_bits = BitArray(bits)
          self.pressure=pressure_bits.int
      def set_temp(self,bits):
          temp_bits = bits[65:97]
          temp_bits = BitArray(bits)
          self.temp=temp.int
      def set_altitude(self, bits):
           altitude_bits = bits[98:130]
           altitude_bits = BitArray(bits)
           altitude=altitude_bits.int

class acceleration:
 
    def __init__(self, bits):
        
        set_time(self,bits)
        set_fsr(self,bits)
        set_x_axis(self,bits)
        set_y_axis(self,bits)
        set_z_axis(self,bits)

    def set_time(self, bits):
        time_bits = bits[0:31]
        time_bits = BitArray(time_bits)
        self.time=time.uint # parse as unsigned?
    def set_fsr(self,bits):
        fsr_bits=bits[32:40]
        fsr_bits=BitArray(fsr_bits)
        self.fsr=fsr_bits.int# unsigned?
    def set_x_axis(self, bits):
        xa_bits = bits[47:64]
        xa_bits= BitArray(xa_bits)
        no_error_correction=xa_bits.int
        self.y_axis=xa.bits/fsr*2^15
    def set_y_axis(self, bits):
        ya_bits = bits[65:80]
        ya_bits = BitArray(ya_bits)
        ya_bits = ya_bits.int
        self.y_axis =  ya.bits/fsr*2^15
             
    def set_z_axis(self,bits):
        za_bits = bits[80:95]
        za_bits = BitArray(za_bits)
        za_bits = ya_bits.int
        self.z_axis =  ya.bits/fsr*2^15
class acceleration:
    def __init__(self, bits):
        set_time(self,bits)
        set_fsr(self,bits)
        set_x_axis(self,bits)
        set_y_axis(self,bits)
        set_z_axis(self,bits)
    def set_time(self, bits):
        time_bits = bits[0:31]
        time_bits = BitArray(time_bits)
        self.time=time.uint # parse as unsigned?
    def set_fsr(self, bits):
        fsr_bits=bits[32:47]
        fsr_bits=BitArray(fsr_bits)
        self.fsr=fsr_bits.int# unsigned?
    def set_x_axis(self, bits):
        av_x_bits = bits[48:63]
        av_x_bits= BitArray(xa_bits)
        av_x_bits = av_x_bits.int
        self.x_axis =  ya.bits/fsr*2^15
             
        
    def set_y_axis(self, bits):
        av_y_bits = bits[64:79]
        av_y_bits = BitArray(av_y_bits)
        av_y_bits = ya_bits.int
        self.y_axis =  ya.bits/fsr*2^15
             
    def set_z_axis(self, bits):
        av_z_bits = bits[80:95]
        av_z_bits = BitArray(za_bits)
        av_z_bits = ya_bits.int
        self.z_axis =  ya.bits/fsr*2^15




class GNSS:
    def __init__(self, bits):
        set_fixtime(self,bits)
        set_lat(self,bits)
        set_long(self,bits)
        set_utc(self,bits)
        set_alt(self,bits)
        set_speed(self,bits)
        set_course(self,bits)
        set_PDOP(self,bits)
        set_VODP(self,bits)
        set_HDOP(self,bits)
        set_sats(self,bits)
        set_fix(self,bits)

    def set_fixtime(bits):
        ft_bits=bits[0:31]
        ft_bits=BitArray(ft_bits)
        self.fix_time=ft_bits.int
    def set_lat(bits):
        lat_bits=bits[32:64]
        lat_bits=BitArray(lat_bits)
        self.lat=lat_bits.int

    def set_long(bits):
        long_bits=bits[64:96]
        long_bits=BitArray(long_bits)
        self.long=long_bits.int
    def set_utc(bits):
        utc_bits=bit[96:128]
        utc_bits=BitArray(long_bits)
        self.utc_time= utc_bits.int

    def set_alt(bits):
        alt_bits=bits[128:160]
        alt_bits=BitArray(alt_bits)
        self.alt=alt_bits.int
    def set_speed(bits):
        speed_bits=bits[160:176]
        speed_bits=BitArray(speed_bits)
        self.speed=speed_bits.int
    def set_course(bits):
        course_bits=bits[176:192]
        course_bits=BitArray(course_bits)
        self.course=course_bits.int
    def set_PDOP(bits):
        PODP_bits=bits[192:208]
        PODP_bits=BitArray(PODP_bits)
        self.PODPs=PODP_bits.int
    def set_HDOP(bits):
        HODP_bits=bits[208:224]
        HODP_bits=BitArray(HODP_bits)
        selfHODP=HODP_bits.int
    def set_VODP(bits):
        VODP_bits=bits[224:240]
        VODP_bits=BitArray(VODP_bits)
        self,VODP=HODP_bits.int
    def set_sats(bits):
        sats_bits=bits[240:247]
        sats_bits=BitArray(sats_bits)
        self.sats=sats_bits.int      
    def set_fix(bits):
        fix_bits=bits[247:248]
        fix_bits=BitArray(fix_bits)
        fix_value=bit.int
        if fix_value==0:
            self.fix='unknown'
        if fix_value==1:
            self.fix= 'not avalible'
        if fix_value==2:
            self.fix = '2d'
        if fix_value==3:
            self.fix = '3d'

class GNSS_Meta:
    Time=0
    gps_sat_in_use=0
    glonass_sats =0
    glonass_sat_enteries =[]
    def __init__(self ,bits):
        set_time(self, bits)
        set_GPS_sats(self, bits)
        set_glonass_sats(self, bits)
        set_dat(self, bits)
    def set_time(self, bits):
        time_bits=bits[0:31]
        time_bits=BitArray(time_bits)
        time_time=time_bits.int
    def set_GPS_sats(self, bits):
        for i in range(0,32):
            if bits[32+i] == 1:
                satcount=satcount+1
        gps_sat_in_use=satcount
    def set_glonass_sats(self,bits):
        GNSS_sats=bits[64:95]
        count =0
        for i in range(0,32):
            if bits[i+64]==1:
                count=count+1
        glonass_sats= count
    def sat_data(bits):
        offset=96
        for i in range (0, glonass_sats+gps_sat_in_use):
           elevation = bits[offset:offset+7]
           elevation = BitArray(elevation)
           elevation = elevation.uint

           snr = bits[offset+8:offset+15]
           snr = BitArray(snr)
           snr= snr.int

           AZ=bits[offset+20:offset+29]
           AZ = BitArray(AZ)
           AZ = AZ.int

           glonas_sat_data=bits[offset+16:offset+20]
           sat_type="type unknown"
           t = bits[offset+31]
           if t ==1:
               type="GLONASS"
           else:
                type = "regular"
           id = bits[offset+16:offset+20]
           gnss_tuple = (elevation, snr, sat_type, AZ , id  )
           glonass_sat_enteries.add(gnss_tuple)

          
           offset=offset+31

class accel:
    time=0
    odr= 0
    fsr=0
    roll=0
    def set_time(bits):
        time_bits=bits[0:31]
        time_bits=BitArray(time_bits)
        time_time=time_bits.int
    def set_odr(bits):
        odr_bits=bits[32+34]
        odr_bits=BitArray(odr_bits)
        odr_bits=odr_bits.int
        if odr_bits== 1:
            odr=0.781
        if odr_bits== 2:
            odr=1.563
        if odr_bits== 3:
            odr=3.125
        if odr_bits==4:
            odr=6.25
        if odr_bits==5:
            odr=25
        if odr_bits ==6:
            odr=50
        if odr_bits==7:
            odr=100
        if odr_bits==8:
            odr=200
        if odr_bits==9:
            odr==400

        if odr_bits==10:
            odr=800
        if odr_bits==11:
            odr=1600
        if odr_bits==12:
            odr=3200
        if odr_bits==13:
            odr=6400
        if odr_bits==14:
            odr=12800
        if odr_bits==15:
            odr=25600
    def set_fsr(bits):
        fsr_bits=bits[35+36]
        fsr_bits=BitArray(fsr_bits)
        fsr_bits=fsr_bits.int
        if fsr_bits==0:
            fsr=8
        if fsr_bits==1:
            fsr=16
        if fsr_bits==2:
            fsr=32
        if sr==3:
            fsr=64
    def set_res(bits):
        res=bits[38]
        if res==0:
            res=8
        if res==1:
            res=16
    def set_roll(bits):
        if bits[37]==0:
            roll="odr/9"
        else:
             roll= "odr/2"
 # todo finish the class           
class IMU_data:
    def __init__(self,bits):
        set_time(self,bits)
    
    def set_time(bits):
        time_bits=bits[0:31]
        time_bits=BitArray(time_bits)
        self.time=time_bits.int
    def set_agsrdiv(self,bits):
        agdiv_bits=bits[32:40]
        agdiv_bits=bits(agdiv_bits)
        self.argdiv=agdiv_bits.int
    def set_ms(self, bits):
        ms_bit=bits[40]
        if ms_bit==0:
            self.sr_mag=8
        else:
            self.sr_mag=100
    def set_afsr(bits):
        afsr_bits=bits[41:43]
        afsr_bits=BitArray(afsr_bits)
        afsr_bits=afsr_bits.int
        self.afsr= 2^afsr_bits
    def set_gfsr(bits):
        gfsr_bits=bits[43:45]
        gfsr_bits=BitArray(gfsr_bits)
        gfsr_bits=gfsr_bits.int
        
        if gfsr_bits==0:
            self.gfsr=250

        if gfsr_bits==1:
            self.gfsr=500
        if gfsr_bits==2:
            self.gfsr=1000
        if gfsr_bits==3:
            self.gfsr=2000
    def set_abw(bits):
        abw_bits=bits[45:47]
        abw_bits=BitArray(abw_bits)
        abw_bits=abw_bits.int
        if abw_bits==0:
            self.abw=5.05
        if abw_bits==1:
            self.abw=10.2
        if abw_bits==2:
            self.abw=21.2
        if abw_bits==3:
            self.abw=44.8
        if abw_bits==4:
            self.abw=99
        if abw_bits==5:
            self.abw=128.1
        if abw_bits==6:
            self.abw=420
    def set_gbw(self,bits):
        gbw_bits=bits[47:49]
        gbw_bits=BitArray(gbw_bits)
        gbw_bits=gbw_bits.int
        if gbw_bits==0:
            self.gbw=5
        if gbw_bits==1:
            self.gbw=10
        if gbw_bits==2:
            self.gbw=20
        if gbw_bits==3:
            self.gbw=41
        if gbw_bits==4:
            self.gbw=91
        if gbw_bits==5:
            self.gbw=128.1
        if gbw_bits==6:
            self.gbw=250
class imu_entry:
    def set_time(bits):
        time_bits=bits[0:31]
        time_bits=BitArray(time_bits)
        self.time=time_bits.int
    
   




    


        


class logger:
    log = {}

    def add(data):
        now = datetime.now()
        log[now.strftime("%H:%M:%S")]=data
                 


def parse_packet(bits):
    offset=96 #skip packet header
    while stop != true :
        #block size
        block_size=bits[]
        block_subtype= bits[offset+10:offset:16]
        block_subtype= BitArray(packet_subtype)
        black_subtype= packet_subtype.int

        if packet_subtype ==3:
            
            a=altitude((BitArray(bits[offset+32:size]))
            logger.add((a,"altitude"))
        elif packet_subtype ==4:
            to_add=acceleration(bits[offset+32:size])
            
            



       
        offset=offset+size



    
        



    

    



        



