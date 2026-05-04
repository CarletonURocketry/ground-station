import logging
import json
from pathlib import Path
from time import time
from fastapi import WebSocket
from ground_station_v2.record import Record
from ground_station_v2.replay import Replay
from ground_station_v2.radio.serial import get_radio_packet
from ground_station_v2.radio.packets.spec import parse_rn2483_transmission
from ground_station_v2.radio.packets.blocks import block_from_csv_row
from ground_station_v2.config import load_config
from ground_station_v2.telemetry_timeline import TelemetryTimelineQueue

logger = logging.getLogger(__name__)

recorder = Record()


# ingest radio packets from the live feed into the live timeline queue
async def ingest_global_radio_packets(live_queue: TelemetryTimelineQueue) -> None:
    config = load_config("config.json")

    try:
        recorder.init_mission("recordings", time())
        recorder.start()

        async for packet in get_radio_packet():
            packet_hex = packet.hex()
            parsed = parse_rn2483_transmission(packet_hex, config)

            if recorder.recording:
                recorder.write(packet_hex, parsed)

            if not parsed:
                logger.warning(f"Failed to parse packet: {packet_hex}")
                continue

            await live_queue.add_blocks(parsed.blocks)

        recorder.stop()
        recorder.close_mission()
    except Exception as e:
        recorder.stop()
        recorder.close_mission()
        logger.error(f"Error in ingest_global_radio_packets: {e}", exc_info=True)

# ingest parsed replay packets from a replay instance and send directly to client WebSocket
async def ingest_client_replay_packets(replay: Replay, websocket: WebSocket) -> None:
    try:
        async for timestamp, row, block_type, _ in replay.run():
            block = block_from_csv_row(timestamp, row, block_type)
            if block:
                await websocket.send_text(json.dumps(block.to_json()))  # type: ignore
    except Exception as e:
        logger.error(f"Error in ingest_client_replay_packets: {e}", exc_info=True)

# ingest parsed replay packets from a recording into the live timeline queue
async def ingest_global_replay_packets(live_queue: TelemetryTimelineQueue, from_recording: Path) -> None:
    try:
        replay_instance = Replay()
        replay_instance.start(from_recording, speed=1.0)
        
        async for timestamp, row, block_type, _ in replay_instance.run():
            block = block_from_csv_row(timestamp, row, block_type)
            if block:
                await live_queue.add_block(block)
    except Exception as e:
        logger.error(f"Error in ingest_global_replay_packets: {e}", exc_info=True)
