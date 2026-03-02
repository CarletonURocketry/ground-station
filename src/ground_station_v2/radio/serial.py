import asyncio
from ground_station_v2.config import load_config
from ground_station_v2.radio.pool import RadioPool
from ground_station_v2.radio.packets.spec import create_fake_packet
import logging

logger = logging.getLogger(__name__)


async def get_radio_packet(fake: bool):
    if fake:
        logger.info("Sending fake radio packet")
        while True:
            yield bytes.fromhex(create_fake_packet())
            await asyncio.sleep(1)
    else:
        config = load_config("config.json")
        pool = RadioPool()

        num_boards = await asyncio.to_thread(pool.discover)

        if num_boards == 0:
            logger.error("No radio boards found. Cannot receive packets.")
            return

        logger.info(f"Setting up {num_boards} radio board(s)")
        await asyncio.to_thread(pool.setup_all, config.radio_parameters)
        logger.info("All radio boards setup complete")

        try:
            async for packet in pool.receive_packets():
                yield packet
        finally:
            pool.close()
