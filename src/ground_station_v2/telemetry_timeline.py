from typing import Optional, Any, Callable
import asyncio
import heapq
import json
import logging

logger = logging.getLogger(__name__)

# This is an auto sorting queue of telemetry samples, the ingestion workers push stuff onto it and the latency workers pop
class TelemetryTimelineQueue:
    def __init__(self, max_size: int = 256):
        self.heap: list[Any] = []
        self.heap_lock = asyncio.Lock()
        self.not_empty = asyncio.Event()
        self.max_size = max_size
    
    async def add_block(self, block: Any) -> None:
        async with self.heap_lock:
            if len(self.heap) >= self.max_size:
                dropped = heapq.heappop(self.heap)
                logger.warning(f"Timeline queue full, dropping oldest block at time {getattr(dropped, 'measurement_time', 'unknown')}")
            
            heapq.heappush(self.heap, block)
            self.not_empty.set()
    
    async def get_next_block(self) -> Optional[Any]:
        async with self.heap_lock:
            if not self.heap:
                self.not_empty.clear()
                return None
            
            block = heapq.heappop(self.heap)
            
            if not self.heap:
                self.not_empty.clear()
            
            return block
    
    async def peek_next_time(self) -> float | None:
        async with self.heap_lock:
            if not self.heap:
                return None
            return self.heap[0].measurement_time
    
    async def wait_for_blocks(self) -> None:
        await self.not_empty.wait()
    
    async def add_blocks(self, blocks: list[Any]) -> None:
        async with self.heap_lock:
            for block in blocks:
                heapq.heappush(self.heap, block)
            
            if self.heap:
                self.not_empty.set()
            
            timestamps = [getattr(b, 'measurement_time', None) for b in self.heap[:10]]
            logger.info(f"Queue size: {len(self.heap)}, first 10 timestamps: {timestamps}")


# This is the worker that simulates the latency of the telemetry to create smoother data
# it pops data from the timeline queue and sends it to the necessary clients based on an internal timer
class TelemetryTimelineWorker:
    def __init__(self, timeline_queue: TelemetryTimelineQueue, get_clients_func: Callable[[], dict[str, Any]]):
        self.timeline_queue = timeline_queue
        self.get_clients_func = get_clients_func
        self.current_mission_time: float = 0.0
        self.speed_multiplier: float = 1.0
    
    async def run(self) -> None:
        await self.timeline_queue.wait_for_blocks()
        first_time = await self.timeline_queue.peek_next_time()
        self.current_mission_time = first_time if first_time is not None else 0.0
        
        import time
        last_real_time = time.time()
        
        while True:
            await asyncio.sleep(0.05)
            
            current_real_time = time.time()
            elapsed_real = current_real_time - last_real_time
            last_real_time = current_real_time
            
            self.current_mission_time += elapsed_real * self.speed_multiplier
            
            blocks_to_send: list[Any] = []
            while True:
                next_time = await self.timeline_queue.peek_next_time()
                if next_time is None or next_time > self.current_mission_time:
                    if next_time is not None and next_time > self.current_mission_time + 1.0:
                        logger.info(f"Gap detected, jumping from {self.current_mission_time:.2f} to {next_time:.2f}")
                        self.current_mission_time = next_time
                    break
                
                block = await self.timeline_queue.get_next_block()
                if block:
                    blocks_to_send.append(block)
            
            if blocks_to_send:
                await self.send_blocks(blocks_to_send)
    
    async def send_blocks(self, blocks: list[Any]) -> None:
        blocks_json = [block.to_json() for block in blocks]
        json_data = json.dumps(blocks_json)
        
        clients = self.get_clients_func()
        
        for client_id, websocket in clients.items():
            try:
                await websocket.send_text(json_data)
            except Exception as e:
                logger.warning(f"Failed to send blocks to client {client_id}: {e}")
