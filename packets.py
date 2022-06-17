from random import randrange

hex_bin_dic = {
              '0': '0000',
              '1': '0001',
              '2': '0010',
              '3': '0011',
              '4': '0100',
              '5': '0101',
              '6': '0110',
              '7': '0111',
              '8': '1000',
              '9': '1001',
              'A': '1010',
              'B': '1011',
              'C': '1100',
              'D': '1101',
              'E': '1110',
              'F': '1111',
              'a': '1010',
              'b': '1011',
              'c': '1100',
              'd': '1101',
              'e': '1110',
              'f': '1111'
              }

bin_hex_dic = {v: k for k, v in hex_bin_dic.items()}

kx134_1211_dic = {
              '0x0': 0.781,
              '0x1': 1.563,
              '0x2': 3.125,
              '0x3': 6.25,
              '0x4': 12.5,
              '0x5': 25,
              '0x6': 50,
              '0x7': 100,
              '0x8': 200,
              '0x9': 400,
              '0xA': 800,
              '0xB': 1600,
              '0xC': 3200,
              '0xD': 6400,
              '0xE': 12800,
              '0xF': 25600,
              '0xa': 800,
              '0xb': 1600,
              '0xc': 3200,
              '0xd': 6400,
              '0xe': 12800,
              '0xf': 25600,
              }


def hex_str_to_int(hex_string):
    return int(hex_string, 16)


def bin_to_hex(bin_string):

    return hex(int(bin_string, 2))


def hex_to_bin(hex_string):
    """better to use this method than the built in 'bin()' method because this method will preserve the number of
       bits. For example bin(0x10) will produce 0b'10000 when we actually want 0b' 00010000"""

    # remove '0x' from start of string, if it's present

    if hex_string[0:2] == '0x':
        hex_string = hex_string[2:]

    ret_string = ''
    for char in hex_string:
        ret_string += hex_bin_dic[char]

    return ret_string


def signed_hex_str_to_int(hex_string,):
    # this function preserves number of bits
    bin_input = hex_to_bin(hex_string)
    if bin_input[0] == '1':
        return int(bin_input[1:], 2) - (2 ** (len(bin_input) - 1))
    else:
        return int(bin_input[1:], 2)


def signed_bin_str_to_int(bin_string):

    return signed_hex_str_to_int(hex(int(bin_string, 2)))


class AltitudeData:

    def __init__(self, raw):
        print('setting altitude data. Raw is ', raw)
        self.time = None
        self.pressure = None
        self.temperature = None
        self.altitude = None

        self.set_time(raw)
        self.set_pressure(raw)
        self.set_temp(raw)
        self.set_altitude(raw)

    def __str__(self):
        return("time:{}\npressure:{}\ntemperature:{}\naltitude:{}\n".format(self.time,
                                                                  self.pressure,
                                                                  self.temperature,
                                                                  self.altitude))

    def set_time(self, raw):
        """
        :param raw: the raw message, a string, that is recieved from the rocket's stack
        :return:
        """

        # time in milliseconds
        self.time = hex_str_to_int(raw[0:8])

    def set_pressure(self, raw):

        # pressure in kilo pascals
        pressure = hex_str_to_int(raw[8:16]) / 1000

        self.pressure = pressure

    def set_temp(self, raw):

        # temperature in recieved in millidegree celcius
        temperature = hex_str_to_int(raw[16:24]) / 1000

        self.temperature = temperature

    def set_altitude(self, raw):

        # altitude in mm
        altitude_mm = hex_str_to_int(raw[24:32])

        altitude_m = altitude_mm / 1000
        self.altitude = altitude_m


class AccelerationData:

    def __init__(self, raw, resolution):

        self.time_stamp = None
        self.fsr = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None

        self.set_time(raw)
        self.set_fsr(raw, resolution)
        self.set_x_axis(raw, resolution)
        self.set_y_axis(raw, resolution)
        self.set_z_axis(raw, resolution)

    def __str__(self):
        return('{}\n{}\n{}\n{}\n{}\n'.format(self.time_stamp,
                                             self.fsr,
                                             self.x_axis,
                                             self.y_axis,
                                             self.z_axis))

    def set_time(self, raw):
        """
        :param raw: the raw message, a string, that is recieved from the rocket's stack
        :return:
        """

        # time in milliseconds
        self.time_stamp = hex_str_to_int(raw[0:8])

    def set_fsr(self, raw, resolution):
        fsr_unadjusted = hex_str_to_int(raw[8:12])
        adjustment_factor = 16 - (resolution + 1)
        self.fsr = (fsr_unadjusted // (2 ** adjustment_factor))

    def set_x_axis(self, raw, resolution):
        #todo: these are signed values and so must be fixed
        measurement = hex_str_to_int(raw[12:16])
        self.x_axis = measurement * (self.fsr / (2 ** 15))

    def set_y_axis(self, raw, resolution):
        measurement = hex_str_to_int(raw[16:20])
        self.y_axis = measurement * (self.fsr / (2 ** 15))

    def set_z_axis(self, raw, resolution):
        measurement = hex_str_to_int(raw[20:24])
        self.y_axis = measurement * (self.fsr / (2 ** 15))


class AngularVelocityData:

    def __init__(self, raw, resolution):

        self.time_stamp = None
        self.fsr = None
        self.x_velocity = None
        self.y_velocity = None
        self.z_velocity = None

        self.set_time(raw)
        self.set_fsr(raw, resolution)
        self.set_x_velocity(raw, resolution)
        self.set_y_velocity(raw, resolution)
        self.set_z_velocity(raw, resolution)

    def set_time(self, raw):
        self.time_stamp = hex_str_to_int(raw[0:8])

    def set_fsr(self, raw, resolution):
        unadjusted_fsr = hex_str_to_int(raw[8:12])

        adjustment_factor = 16 - (resolution + 1)

        self.fsr = unadjusted_fsr // (2 ** adjustment_factor)

    def set_x_velocity(self, raw, resolution):
        measurement = hex_str_to_int(raw[12:16])
        self.x_velocity = measurement * (self.fsr / (2 ** 15))

    def set_y_velocity(self, raw, resolution):
        measurement = hex_str_to_int(raw[16:20])
        self.y_velocity = measurement * (self.fsr / (2 ** 15))

    def set_z_velocity(self, raw, resolution):
        measurement = hex_str_to_int(raw[20:24])
        self.z_velocity = measurement * (self.fsr / (2 ** 15))

    def __str__(self):
        return('fsr: {}\nx_velocity: {}\ny_velocity: {}\nz_velocity: {}\n'.format(self.fsr,
                                                                                  self.x_velocity,
                                                                                  self.y_velocity,
                                                                                  self.z_velocity))


class GNSSMetaData:

    class Info:
        """stores metadata on satellites used in the GNSS"""
        def __init__(self, raw):

            # elevation of GNSS satellite in degrees
            self.elevation = None

            # signal to noise ratio in dB Hz
            self.SNR = None

            # the pseudo-random noise sequence for GPS satellites or the ID for GLONASS satellites
            self.ID = None

            # satellite's azimuth in degrees
            self.azimuth = None

            # the type of satellite (GPS or GLONASS)
            self.type = None

            # set up all parameters
            self.setup(raw)

        def setup(self, raw):

            self.elevation = int(raw[0:8], 2)
            self.SNR = int(raw[8:16], 2)

            self.ID = int(raw[16:21], 2)
            self.azimuth = int(raw[21:30], 2)

            # check to see if the type bit is 1 or 0
            if raw[31] == '1':
                self.type = 'GLONASS'
            else:
                self.type = 'GPS'

        def __str__(self):

            return ('elevation: {}\n'
                    'SNR: {}\n'
                    'ID: {}\n'
                    'Azimuth: {}\n'
                    'type: {}\n'.format(self.elevation, self.SNR, self.ID, self.azimuth, self.type))

    def __init__(self, raw):
        self.mission_time = None
        self.gps_sats_in_use = []
        self.glonass_sats_in_use = []
        self.sat_info = {}
        self.setup(raw)

    def setup(self, raw):
        self.mission_time = hex_str_to_int(raw[0:8])

        # convert to binary
        bin_raw = bin(int(raw, 16))

        bin_GPS_sats_in_use = bin_raw[34:66]
        bin_GLONASS_sats_in_use = bin_raw[66:98]

        # figure out which satellites are in use
        for i in range(32):

            if bin_GPS_sats_in_use[i] == '1':
                self.gps_sats_in_use.append(i + 1)

            if bin_GLONASS_sats_in_use[i] == '1':
                self.glonass_sats_in_use.append(i + 1)

        # parse information about the satellites
        sat_info = bin_raw[98:]

        num_sats = len(sat_info) // 32

        for i in range(num_sats):
            # each satellite's info is stored in 32 bits
            meta_data = self.Info(sat_info[i*32: i*32 + 32])
            self.sat_info[meta_data.ID] = meta_data


class GNSSLocationData:

    def __init__(self, raw):

        # mission time when fix was received
        self.fix_time = None

        # latitude in units of 100u' (100 micro arcminute) or 10^-4 arc minutes per least significant bit
        self.latitude = None

        # latitude in units of 100u' (100 micro arcminute) or 10^-4 arc minutes per least significant bit
        self.longitude = None

        # the time (in UTX) when the fix was received in seconds since the Unix apoch
        self.utc_time = None

        # millimeters above sea level
        self.altitude = None

        # speed of the rocket over the ground in units of 1/100th of a knot
        self.rocket_speed = None

        # course of rocket in units of 1/100th of a degree
        self.rocket_course = None

        # position dilution of precision * 100
        self.pdop = None

        # horizontal dilution of precision * 100
        self.hdop = None

        # veritcal dilution of precision * 100
        self.vdop = None

        # number of GNSS satellites used to get this fix
        self.num_sats = None

        # the type of fix, can be either 'unknown', 'not available', '2D fix', or '3D fix'
        self.fix_type = None

        self.setup(raw)

    def setup(self, raw):
        print(raw)

        self.fix_time = hex_str_to_int(raw[0:8])
        self.latitude = signed_hex_str_to_int(raw[8:16])
        self.longitude = signed_hex_str_to_int((raw[16:24]))
        self.utc_time = hex_str_to_int(raw[24:32])
        self.altitude = hex_str_to_int(raw[32:40])

        self.rocket_speed = signed_hex_str_to_int(raw[40:44])
        self.rocket_course = signed_hex_str_to_int(raw[44:48])
        self.pdop = hex_str_to_int(raw[48:52])
        self.hdop = hex_str_to_int(raw[52:56])

        self.vdop = hex_str_to_int(raw[56:60])
        self.num_sats = hex_str_to_int(raw[60:62])

        fix_type_temp = hex_to_bin(raw[62:])
        fix_type_temp = fix_type_temp[2:4]
        fix_type = int(fix_type_temp, 2)

        if fix_type == 0:
            self.fix_type = 'unknown'
        elif fix_type == 1:
            self.fix_type = 'not available'
        elif fix_type == 2:
            self.fix_type = '2D fix'
        elif fix_type == 3:
            self.fix_type = '3D fix'
        else:
            self.fix_type = 'error'

    def __str__(self):
        return('fix time: {}\n'
               'latitude: {}\n'
               'longitude: {}\n'
               'utc_time: {}\n'
               'altitude: {}\n'
               'rocket speed: {}\n'
               'rocket_course: {}\n'
               'pdop: {}\n'
               'hdop: {}\n'
               'vdop: {}\n'
               'num_sats: {}\n'
               'fix_type: {}\n'.format(self.fix_time,
                                       self.latitude,
                                       self.longitude,
                                       self.utc_time,
                                       self.altitude,
                                       self.rocket_speed,
                                       self.rocket_course,
                                       self.pdop,
                                       self.hdop,
                                       self.vdop,
                                       self.num_sats,
                                       self.fix_type))


class MPU9250Data:
    """data from the MPU9250 IMU"""

    class Measurement:

        def __init__(self, raw_bin):

            print(raw_bin)
            self.time_stamp = int(raw_bin[0:32], 2)
            self.accel_x = int(raw_bin[32:48], 2)
            self.accel_y = int(raw_bin[48:64], 2)
            self.accel_z = int(raw_bin[64:80], 2)
            self.temperature = int(raw_bin[80:96], 2)

            self.gyro_x = int(raw_bin[96:112], 2)
            self.gyro_y = int(raw_bin[112:128], 2)
            self.gyro_z = int(raw_bin[128:144], 2)

            self.mag_x = int(raw_bin[144:160], 2)
            self.mag_y = int(raw_bin[160:176], 2)
            self.mag_z = int(raw_bin[176:192], 2)

            self.mag_valid = int(raw_bin[195], 2)
            self.mag_resolution = int(raw_bin[196], 2)

        def __str__(self):
            return "time: {}\n" \
                   "temperature: {}\n" \
                   "accel x: {}\n" \
                   "accel y: {}\n" \
                   "accel z: {}\n" \
                   "gyro x: {}\n" \
                   "gyro y: {}\n" \
                   "gyro z: {}\n" \
                   "mag x: {}\n" \
                   "mag y: {}\n" \
                   "mag z: {}\n" \
                   "mag valid: {}\n" \
                   "mag resolution: {}\n".format(self.time_stamp,
                                                 self.temperature,
                                                 self.accel_x,
                                                 self.accel_y,
                                                 self.accel_z,
                                                 self.gyro_x,
                                                 self.gyro_y,
                                                 self.gyro_z,
                                                 self.mag_x,
                                                 self.mag_y,
                                                 self.mag_z,
                                                 self.mag_valid,
                                                 self.mag_resolution)

    def __init__(self, raw):
        self.time_stamp = None

        # sample rate of the accelerometer and gyroscope
        self.ag_sample_rate = None

        # accelerometer full scale range
        self.accelerometer_fsr = None

        # gyroscope full scale range
        self.gyroscope_fsr = None

        # bandwidth for the low pass filter used by the accelerometer
        self.accelerometer_bw = None

        # bandwidth for the low pass filter used by the gyroscope
        self.gyroscope_bw = None

        self.setup(raw)

    def setup(self, raw):
        self.time_stamp = hex_str_to_int(raw[0:8])

        self.ag_sample_rate = hex_str_to_int(raw[8:10])

        raw_bin = hex_to_bin(raw)

        # get the fsr of the accelerometer
        raw_a_fsr = int(raw_bin[39:41], 2)
        self.accelerometer_fsr = 2** (raw_a_fsr + 1)

        #TODO: this needs to be finished after we recieve an input from this device


class KX1341211Data:

    class Measurement:
        def __init__(self, raw):
            self.x_accel = None
            self.y_accel = None
            self.z_accel = None

            self.setup(raw)

        def setup(self, raw):
            # if resolution of data is 8 bit (three 8 bit readings)
            if len(raw) == 24:
                self.x_accel = signed_bin_str_to_int(raw[0:8])
                self.y_accel = signed_bin_str_to_int(raw[8:16])
                self.z_accel = signed_bin_str_to_int(raw[16:24])

            # if resolution of data is 16 bit (three 16 bit readings)
            elif len(raw) == 48:
                self.x_accel = int(raw[0:16], 2)
                self.y_accel = int(raw[16:32], 2)
                self.z_accel = int(raw[32:48], 2)

        def __str__(self):
            return ('x: {}\n'
                    'y: {}\n'
                    'z: {}\n'.format(self.x_accel,
                                     self.y_accel,
                                     self.z_accel))

    def __init__(self, raw):

        self.time_stamp = None

        # data rate of the accelerometer in Hz
        self.data_rate = None

        # set the full scale range (in G's)
        self.full_scale_range = None

        # the corner frequency of the accelerometer's low pass filter (in Hz)
        self.corner_freq = None

        # the actual measurements taken by the accelerometer
        self.measurements = []

        self.setup(raw)

    def __str__(self):

        data_points_str = ''
        for m in self.measurements:
            data_points_str += str(m)
            data_points_str += '____\n'

        return('time stamp: {}\n'
               'data rate: {}\n'
               'full scale range: {}\n'
               'corner frequency: {}\n'
                'measurements:\n{}'
               '______________________'.format(self.time_stamp,
                                               self.data_rate,
                                               self.full_scale_range,
                                               self.corner_freq,
                                               data_points_str)
               )

    def setup(self, raw):

        raw_bin = hex_to_bin(raw)

        self.time_stamp = int(raw_bin[0:32], 2)

        # data rate of the accelerometer in Hz
        data_rate = hex(int(raw_bin[32:36], 2))
        self.data_rate = kx134_1211_dic[data_rate]

        # set the full scale range (in G's)
        full_scale_range = int(raw_bin[36:38], 2)

        if full_scale_range == 0:
            self.full_scale_range = 8
        elif full_scale_range == 1:
            self.full_scale_range = 16
        elif full_scale_range == 2:
            self.full_scale_range = 32
        elif full_scale_range == 3:
            self.full_scale_range = 64
        else:
            self.full_scale_range = -1

        # the corner frequency of the accelerometer's low pass filter (in Hz)
        corner_freq = raw_bin[38]

        if corner_freq == '0':
            self.corner_freq = self.data_rate / 9
        elif corner_freq == '1':
            self.corner_freq = self.data_rate / 2

        # resolution of the accelerometer reading (in bits)
        resolution = raw_bin[39]

        if resolution == '0':
            resolution = 8
        elif resolution == '1':
            resolution = 16

        print('resolution is ', resolution)

        # number of bits of padding added to the end of the data packet
        padding = int(raw_bin[46:48], 2) * 8
        print('padding is ', padding)

        accel_data = raw_bin[48:]

        chunk_size = resolution * 3

        # break the accel data into chunks that contain acceleration in the x y and z directions
        accel_data = [accel_data[i:i + chunk_size] for i in range(0, (len(accel_data) - padding), chunk_size)]

        print(accel_data)
        for data in accel_data:
            self.measurements.append(self.Measurement(data))
