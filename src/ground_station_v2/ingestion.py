import logging
import json
from pathlib import Path
from time import time
from fastapi import WebSocket
from ground_station_v2.record import Record
from ground_station_v2.replay import Replay
from ground_station_v2.radio.serial import get_radio_packet
from ground_station_v2.radio.packets.spec import parse_rn2483_transmission
from ground_station_v2.radio.packets.blocks import Block, block_from_csv_row, DerivedFlightMetrics
from ground_station_v2.config import load_config
from ground_station_v2.telemetry_timeline import TelemetryTimelineQueue

logger = logging.getLogger(__name__)

recorder = Record()

class _IngestionProcessor():
    def __init__(self):
        """Initialize instance variables"""
        self.apogee : float = 0
        self.last_two_altitudes : list[tuple[float, float]] = []
        self.speed : float = 0
        self.max_speed : float = 0
        self.gps_lock : bool = False
    
    def process_block(self, block: Block) -> DerivedFlightMetrics | None:
        """
        Derives data from telemetry blocks based on sensor_type.
        Returns a list of blocks: original block + derived metrics block if applicable.
        """
        try:
            block_json = block.to_json()
            sensor_type = block_json.get("sensor_type")
            measurement_time : float = block_json.get("measurement_time", 0.0)
        except Exception as e:
            logger.debug(f"Failed to extract sensor_type from block: {e}")
            return None
        
        if sensor_type == "altitude_sea_level":
            self._process_altitude(block)
        elif sensor_type == "gnss":
            self._process_gnss(block)
        else:
            return None
        
        # Emit derived metrics block
        derived_block = DerivedFlightMetrics(
            measurement_time = int(measurement_time),
            apogee = self.apogee,
            altitude_rate = self.speed,
            max_altitude_rate = self.max_speed,
            gps_lock = self.gps_lock
        )
        
        return derived_block
    
    def _process_altitude(self, block: Block) -> None:
        """
        Update apogee and altitude history for speed calculation.
        """
        if not hasattr(block, "altitude") or not hasattr(block, "measurement_time"):
            return
        
        try:
            altitude = float(block.altitude)
            timestamp = float(block.measurement_time)
        except (ValueError, TypeError):
            return
        
        if altitude > self.apogee:
            self.apogee = altitude
        
        self.last_two_altitudes.append((timestamp, altitude))
        if len(self.last_two_altitudes) > 2:
            self.last_two_altitudes.pop(0)
        
        if len(self.last_two_altitudes) == 2:
            (t1, a1), (t2, a2) = self.last_two_altitudes
            dt = t2 - t1
            if dt > 0:
                self.speed = (a2 - a1) / dt
                if abs(self.speed) > self.max_speed:
                    self.max_speed = abs(self.speed)
    
    def _process_gnss(self, block: Block) -> None:
        """
        Update GPS lock status from GNSS block.
        """
        # Extract lock status if available in the block
        # TODO: Check actual GNSS block structure and update self.gps_lock
        pass

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


                #_IngestionProcessor.process_block(block)


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

                #_IngestionProcessor.process_block(block)


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
