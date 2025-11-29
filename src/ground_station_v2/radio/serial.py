import asyncio
from src.ground_station_v2.config import load_config
from src.ground_station_v2.radio.rn2483 import RN2483Radio
from src.ground_station_v2.radio.packets.spec import create_fake_packet
import logging

logger = logging.getLogger(__name__)

def discover_port():
    logger.error("Not implemented")
    return ""

async def get_radio_packet(fake: bool):
    # TODO: remove this, just for testing
    # port = "/dev/tty.usbserial-DP05O1XX"

    if fake:
        logger.info("Sending fake radio packet")
        while True:
            logger.info("Sending packet")
            yield bytes.fromhex(create_fake_packet())
            await asyncio.sleep(1)
    else:
        port = discover_port()
        config = load_config("config.json")
        radio = RN2483Radio(port)
        
        logger.info(f"Setting up radio on port {port}")
        await asyncio.to_thread(radio.setup, config.radio_parameters)
        logger.info("Radio setup complete")

        logger.info("Receiving radio packets")
        while True:
            message = await asyncio.to_thread(radio.receive)
            logger.info(f"Received radio packet: {message}")
            if message:
                yield bytes.fromhex(message)