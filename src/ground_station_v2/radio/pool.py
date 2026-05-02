"""
Radio pool for managing multiple radio boards.

Discovers connected serial devices, identifies supported radio modules,
and reads from all boards concurrently to minimize missed packets.
Duplicate packets received by multiple boards are automatically filtered.
"""

import asyncio
import hashlib
import logging
import os
import platform
import time
from typing import AsyncGenerator

from serial import Serial, EIGHTBITS, PARITY_NONE, SerialException

from ground_station_v2.config import RadioParameters
from ground_station_v2.radio.rn2483 import RN2483Radio, RN2483_BAUD

logger = logging.getLogger(__name__)

IDENTIFY_TIMEOUT: float = 3.0  # Seconds to wait for an identification response
DEDUP_WINDOW: float = 2.0  # Seconds to keep packet hashes for deduplication

# Serial port prefixes by platform
_PORT_PREFIXES: dict[str, list[str]] = {
    "Darwin": ["tty.usbserial"],
    "Linux": ["ttyUSB", "ttyACM"],
}


def scan_serial_ports() -> list[str]:
    """Scan /dev for serial ports that could be radio boards."""
    system = platform.system()
    prefixes = _PORT_PREFIXES.get(system, ["tty.usbserial", "ttyUSB"])

    if not os.path.isdir("/dev"):
        logger.error(
            "/dev directory not found. This likely means you are running on Windows, which is not supported. Please use macOS, Linux, or a UNIX based system."
        )

        return []

    try:
        files = os.listdir("/dev")
    except OSError:
        logger.error("Could not list /dev directory")
        return []

    ports: list[str] = []
    for file in files:
        for prefix in prefixes:
            if file.startswith(prefix):
                ports.append(f"/dev/{file}")
                break

    return ports


def is_rn2483(port: str) -> bool:
    """Check whether an RN2483 radio module is connected on the given serial port.

    Sends the ``sys get ver`` command and checks that the response starts
    with ``RN2483``.
    """
    conn = None
    try:
        conn = Serial(
            port=port,
            baudrate=RN2483_BAUD,
            bytesize=EIGHTBITS,
            parity=PARITY_NONE,
            stopbits=1,
        )
        conn.timeout = IDENTIFY_TIMEOUT

        conn.reset_input_buffer()
        conn.reset_output_buffer()

        conn.write(b"sys get ver\r\n")

        response = conn.readline().decode("utf-8", errors="ignore").strip()
        conn.close()

        # The response from the radio module after the sent command "sys get ver" should start with "RN2483" for it to be a valid module.
        if response.startswith("RN2483"):
            logger.info(f"Identified RN2483 on {port}: {response}")
            return True

    except (SerialException, OSError) as e:
        logger.debug(f"Could not identify device on {port}: {e}")
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    return False


class RadioPool:
    """Manages a pool of radio boards for redundant packet reception.

    On startup, discovers and identifies all connected radio boards. During
    operation, reads from every board concurrently. If multiple boards receive
    the same packet, duplicates are filtered so only one copy is yielded.
    """

    def __init__(self) -> None:
        self.radios: list[tuple[str, RN2483Radio]] = []  # (port, radio)
        self._packet_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._seen_packets: dict[str, float] = {}  # hash -> monotonic timestamp
        self._receiver_tasks: list[asyncio.Task[None]] = []

    def discover(self) -> int:
        """Scan serial ports and identify radio boards.

        Identified boards are added to the pool. This is a blocking call
        (should be run via asyncio.to_thread from async code).

        Returns:
            The number of boards added to the pool.
        """
        ports = scan_serial_ports()
        logger.info(f"Scanning {len(ports)} serial port(s): {ports}")

        for port in ports:
            if is_rn2483(port):
                radio = RN2483Radio(port)
                self.radios.append((port, radio))
                logger.info(f"Added RN2483 on {port} to radio pool")
            else:
                logger.debug(f"No RN2483 module found on {port}")

        logger.info(f"Radio pool: {len(self.radios)} board(s) discovered")
        return len(self.radios)

    def setup_all(self, parameters: RadioParameters) -> None:
        """Set up all radios in the pool with the given parameters.

        This is a blocking call (should be run via asyncio.to_thread from async code).
        """
        for port, radio in self.radios:
            try:
                radio.setup(parameters)
                logger.info(f"Setup complete for RN2483 on {port}")
            except SerialException as e:
                logger.error(f"Failed to set up RN2483 on {port}: {e}")

    def _is_duplicate(self, packet_hash: str) -> bool:
        """Check if a packet with this hash was seen within the dedup window."""
        now = time.monotonic()

        # Purge expired entries. Loops for each seen packet and checks if it's within the dedup window.
        expired = [h for h, t in self._seen_packets.items() if now - t > DEDUP_WINDOW]
        for h in expired:
            del self._seen_packets[h]

        if packet_hash in self._seen_packets:
            return True

        self._seen_packets[packet_hash] = now
        return False

    async def _receive_from_radio(self, port: str, radio: RN2483Radio) -> None:
        """Continuously receive from one radio and enqueue packets."""
        logger.info(f"Starting receiver for RN2483 on {port}")
        while True:
            try:
                message = await asyncio.to_thread(radio.receive)
                if message:
                    packet_bytes = bytes.fromhex(message)
                    await self._packet_queue.put(packet_bytes)
            except Exception as e:
                logger.error(f"Error receiving from RN2483 on {port}: {e}")
                await asyncio.sleep(1)

    async def receive_packets(self) -> AsyncGenerator[bytes, None]:
        """Yield deduplicated packets from all radios in the pool.

        Starts a concurrent receiver task per radio board. Packets seen by
        multiple boards within the dedup window are yielded only once.
        """
        for port, radio in self.radios:
            task = asyncio.create_task(self._receive_from_radio(port, radio))
            self._receiver_tasks.append(task)

        try:
            while True:
                packet = await self._packet_queue.get()
                packet_hash = hashlib.sha256(packet).hexdigest()

                if self._is_duplicate(packet_hash):
                    logger.debug("Duplicate packet filtered")
                    continue

                yield packet
        finally:
            for task in self._receiver_tasks:
                task.cancel()
            self._receiver_tasks.clear()

    def close(self) -> None:
        """Close all radio connections in the pool."""
        for port, radio in self.radios:
            try:
                radio.serial.close()
                logger.info(f"Closed RN2483 on {port}")
            except Exception as e:
                logger.error(f"Error closing RN2483 on {port}: {e}")
        self.radios.clear()
