# Authors: Matteo Golin
# Imports
import queue
import packets

# Constants
SUBTYPE = {
    3: "altitude_data",
    4: "acceleration_data",
    5: "angular_velocity_data",
    6: "GNSS_location_data",
    7: "GNSS_metadata",
    8: "power_information",
    9: "temperatures",
    "A": "MPU9250_IMU_data",
    "B": "KX134-1211_accelerometer_data"
}

PACKETS = {
    SUBTYPE[3]: packets.AltitudeData,
    SUBTYPE[4]: packets.AccelerationData,
    SUBTYPE[5]: packets.AngularVelocityData,
    SUBTYPE[6]: packets.GNSSLocationData,
    SUBTYPE[7]: packets.GNSSMetaData,
    SUBTYPE["A"]: packets.MPU9250Data,
    SUBTYPE["B"]: packets.KX1341211Data
}


# Functions
def _parse_packet_header(header) -> tuple:

    """
    Returns the packet header string's informational components in a tuple.

    length: int
    version: int
    src_addr: int
    packet_num: int
    """

    # Extract call sign in hex
    call_sign: str = header[0:12]

    # Convert header from hex to binary
    header = bin(int(header, 16))

    # Extract values and then convert them to ints
    length: int = (int(header[47:53], 2) + 1) * 4
    version: int = int(header[53:58], 2)
    src_addr: int = int(header[63:67], 2)
    packet_num: int = int(header[67:79], 2)

    return call_sign, length, version, src_addr, packet_num


def _parse_block_header(header) -> tuple:

    """
    Parses a block header string into its information components and returns them in a tuple.

    block_len: int
    crypto_signature: bool
    message_type: int
    message_subtype: str
    destination_addr: int
    """

    header = bin(int(header, 16))  # Convert into binary

    block_len: int = int(header[0:5], 2) - 4  # Length of block in bytes, excluding header, hence subtract 4
    crypto_signature: bool = True if int(header[5], 2) == 1 else False  # Check if message has a cryptographic signature

    # Type of message (Ex: The purpose of the block, such as transmitting info to ground station)
    message_type: int = int(header[6:10], 2)

    message_subtype: str = SUBTYPE.get(int(header[10:16], 2))  # Type of information that is stored in the block
    destination_addr: int = int(header[16:20], 2)

    return block_len, crypto_signature, message_type, message_subtype, destination_addr


def parse_rx(data: queue.Queue | str) -> tuple | None:

    # Data is a string
    if type(data) == str:
        header_length = 12

    # Data is a queue
    else:
        header_length = 24

        if data.empty():
            return None
        else:
            data = data.get()

    # Extract the packet header
    call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

    if length <= header_length:  # If this packet nothing more than just the  header
        return call_sign, length, version, srs_addr, packet_num

    blocks = data[24:]  # Remove the packet header

    # Parse through all blocks
    while blocks != '':

        # Parse block header
        block_header = blocks[:8]
        block_len, crypto_signature, message_type, message_subtype, dest_addr = _parse_block_header(block_header)

        block_len = block_len * 2  # Convert length in bytes to length in hex symbols
        payload = blocks[8: 8 + block_len]

        # Create data if correct packet format was found
        packet = PACKETS.get(message_subtype)
        packet_data = packet.create_from_raw(payload) if packet else None

        # Remove the data we processed from the whole set, and move onto the next data block
        blocks = blocks[8 + block_len:]


# Random previous commented code with no explanation
# q = queue.Queue()
# q.put('123456781234567812345678F0F0F0F0FFFFFFFF00000000FFFFFFFFAABB\r\n')
# res = parse_rx(q)
# print(res)
