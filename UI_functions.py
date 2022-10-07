import queue
import packets


def _parse_packet_header(header):

    # extract call sign in hex
    call_sign = header[0:12]

    # convert header from hex to binary
    header = bin(int(header, 16))

    # extract values and then convert them to ints
    length = (int(header[47:53], 2) + 1 ) * 4
    version = int(header[53:58], 2)
    src_addr = int(header[63:67], 2)
    packet_num = int(header[67:79], 2)

    print( call_sign, length, version, src_addr, packet_num)


def _parse_block_header(header):

    # convert into binary
    header = bin(int(header, 16))

    # length of block in bytes (excluding header (that's why we subtract 4))
    block_len = int(header[0:5], 2) - 4

    # does the message have a cryptographic signature?
    sig = int(header[5], 2)
    if sig == 1:
        sig = True
    else:
        sig = False

    # type of message (ie. the purpose of the block, ie. to transmit info to ground station)
    type = int(header[6:10], 2)

    # the type of information that is stored in the block
    subtype = int(header[10:16], 2)

    dest_addr = int(header[16:20], 2)

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

    return block_len, sig, type, subtype, dest_addr


def parse_rx(q:queue.Queue):

    if q.empty():
        return
    else:
        data = q.get()

    # extract the packet header
    call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

    # if this packet nothing more than just the packet header
    if length <= 24:
        return [call_sign, length, version, srs_addr, packet_num]

    # remove the packet header
    blocks = data[24:]
    # parse through all blocks
    while blocks != '':
        block_header = blocks[:8]

        block_len, sig, _type, _subtype, dest_addr = _parse_block_header(block_header)

        # convert length in bytes to length in hex symbols
        block_len = block_len * 2

        payload = blocks[8: 8 + block_len]

        if _subtype == 'altitude_data':
            data = packet.AltitudeData(payload)

        elif _type == 'acceleration_data':
            data = packet.AccelerationData(payload)

        elif _type == 'angular_velocity_data':
            data = packet.AngularVelocityData(payload)

        elif _type == 'GNSS_location_data':
            data = packet.GNSSLocationData(payload)

        elif _type == 'GNSS_metadata_data':
            data = packet.GNSSMetaData(payload)

        elif _type == 'MPU9250_IMU_data_data':
            data = packet.MPU9250Data(payload)

        elif _type == 'KX134-1211_accelerometer_data':
            data = packet.KX1341211Data(payload)

        else:
            data = -1

        # remove the data we processed from the whole set, and move onto the next data block
        blocks = blocks[8 + block_len:]

def _parse_rx(data):

    # extract the packet header
    call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

    # if this packet nothing more than just the packet header
    print(length)
    if length <= 12:  # length less than 12 bytes
        return [call_sign, length, version, srs_addr, packet_num]

    # remove the packet header (it's in hex, and since there are two hex symbols per byte, we remove 24 hex symbols)
    blocks = data[24:]
    # parse through all blocks

    datas = []

    while blocks != '':
        block_header = blocks[:8]

        block_len, sig, _type, _subtype, dest_addr = _parse_block_header(block_header)

        # convert length in bytes to length in hex symbols
        block_len = block_len * 2

        payload = blocks[8: 8 + block_len]

        if _subtype == 'altitude_data':
            data = packet.AltitudeData(payload)

        elif _type == 'acceleration_data':
            data = packet.AccelerationData(payload)

        elif _type == 'angular_velocity_data':
            data = packet.AngularVelocityData(payload)

        elif _type == 'GNSS_location_data':
            data = packet.GNSSLocationData(payload)

        elif _type == 'GNSS_metadata_data':
            data = packet.GNSSMetaData(payload)

        elif _type == 'MPU9250_IMU_data_data':
            data = packet.MPU9250Data(payload)

        elif _type == 'KX134-1211_accelerometer_data':
            data = packet.KX1341211Data(payload)

        else:
            data = -1

        print(data)
        # remove the data we processed from the whole set, and move onto the next data block
        blocks = blocks[8 + block_len:]


# q = queue.Queue()
# q.put('123456781234567812345678F0F0F0F0FFFFFFFF00000000FFFFFFFFAABB\r\n')
# res = parse_rx(q)
# print(res)