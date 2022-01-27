from random import randrange
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
        set_agsrdiv(self,bits)
        set_ms(self,bits)
        set_afsr(self,bits)
        set_gfsr(self,bits)
        set_abw(self,bits)
        set_gbw(self,bits)
        set_abw(self,bits)
    
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
        mag_data = []
        gyro_data = []
        for i in range (0,3):
            acell_bits=bits[offset:offset+16]
            acell_bits=BitArray(acell_bits)
            acell=acell_bits.int
            acell_data.append(acell)
            range+16
        self.acell_arr=acell_data  
        for i in range (0,3):
            gyro_bits=bits[offset:offset+16]
            gyro_bits=BitArray(gyro_bits)
            gyro_data.append(gyro)
            range+16

        self.gyro_arr=gyro_data
        for i in range (0,3):
            mag_bits=bits[offset:offset+16]
            mag_bits=BitArray(mag_bits)
            mag_data.append(mag)
            range+16

        self.mag_arr=mag_data   
    def set_res(self,bits):
        if bits[163]==0:
            self.res=16
        else: 
            self.res=14    
    def set_overflow(self,bits):
        if bits[164]==1:
            self.overflow="yes"    
        else:
            self.overflow="no"
    
   

    

def test_sending_data():
 data = {
  "state": "undefined ",
  "chute deployed": 30,
  "mission time": 0,
  "latitude" : 0.0000,
  "longditude" : 0.0000, 
   "altitude " : 0 ,
   "spped" : 0.00,
   "course" : "undefined",
   "time"  : 0.00, 
   "altitude " : 0.00,
   "temp" : 0.000,
   "x": 0 ,
   "y": 0 ,
   "z" : randrange(10),
   "temp" : randrange(10)
   
 }
 return data 

   




    

    



        



