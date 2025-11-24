# Tornado websocket for UI communication
# This is PURELY a pass through of data for connectivity. No format conversion is done here.
# Incoming information comes from telemetry_json_output from telemetry
# Outputs information to connected websocket clients
#
# Authors:
# Thomas Selwyn (Devil)

from __future__ import annotations
import json
from multiprocessing import Queue, Process
from abc import ABC
from typing import Optional, Any
import logging
import os.path
import uuid
import tornado.ioloop
import tornado.web
import tornado.websocket

# Constants
ws_commands_queue: Queue[Any]

# Logger
logger = logging.getLogger(__name__)


class WebSocketHandler(Process):
    """Handles starting the websocket server process."""

    def __init__(self, telemetry_json_output: Queue[Any], ws_commands: Queue[Any]):
        super().__init__()
        global ws_commands_queue

        self.telemetry_json_output: Queue[Any] = telemetry_json_output
        ws_commands_queue = ws_commands

        # Default to test mode
        # ws_commands_queue.put("serial rn2483_radio connect test")

        self.start_websocket_server()

    def start_websocket_server(self) -> None:
        """Starts up the websocket server."""

        wss = tornado.web.Application(
            [
                (r"/websocket", TornadoWSServer),
                (
                    r"/(.*)",
                    tornado.web.StaticFileHandler,
                    {"path": os.path.join(os.getcwd(), "static"), "default_filename": "test.html"},
                ),
            ],
            websocket_ping_interval=5,
            websocket_ping_timeout=10,
        )

        try:
            _ = wss.listen(33845, address="0.0.0.0")
            logger.info("HTTP listening on port 33845, accessible at http://localhost:33845")
        except OSError:
            logger.error("Failed to bind to port 33845, ensure there is no other running ground station process!")
            ws_commands_queue.put("shutdown")

        io_loop = tornado.ioloop.IOLoop.current()
        periodic_callback = tornado.ioloop.PeriodicCallback(
            lambda: TornadoWSServer.send_message(self.check_for_messages()), 50
        )

        periodic_callback.start()
        io_loop.start()

    def check_for_messages(self) -> Optional[str]:
        """Returns any JSON data that may be on the telemetry JSON output queue."""

        json_data = None
        while not self.telemetry_json_output.empty():
            json_data = self.telemetry_json_output.get()
        return json.dumps(json_data)


class TornadoWSServer(tornado.websocket.WebSocketHandler, ABC):
    """The server which handles websocket connections."""

    # Clients now have a client ID
    clients: dict[str, TornadoWSServer] = {}
    last_msg_send: str = ""

    def open(self, *args: Any, **kwargs: Any) -> None:
        # Generate unique client ID using UUID4
        # This should make sure that there are no duplicate client IDs
        # UUID4 has been proven to be so unbelievably unlikely to have duplicates that people don't even bother considering it, so this is very good for our use case
        self.client_id = str(uuid.uuid4())
        TornadoWSServer.clients[self.client_id] = self
        self.send_message(self.last_msg_send)
        logger.info(f"Client connected with ID: {self.client_id}")

    def on_close(self) -> None:
        # Safety check: client_id might not be set if connection failed during open()
        if not hasattr(self, 'client_id'):
            logger.warning("Client disconnected before client_id was assigned")
            return
            
        if self.client_id in TornadoWSServer.clients:
            del TornadoWSServer.clients[self.client_id]
        # Notify telemetry to stop any active replay for this client
        ws_commands_queue.put(f"__client_id__{self.client_id} telemetry replay stop")
        logger.info(f"Client disconnected: {self.client_id}")

    def on_message(self, message: str | bytes) -> None:
        message = str(message)
        logger.info(f"Received message: {message}")

        # Put client id at the start of the command for tracking which client sent it
        ws_commands_queue.put(f"__client_id__{self.client_id} {message}")

    def check_origin(self, origin: str) -> bool:
        """Authenticates clients from any host origin (_ parameter)."""
        return True

    @classmethod
    def send_message(cls, message: str | None) -> None:
        if message is None or message == "null":
            return

        cls.last_msg_send = message
        
        # Parse message to check for target field
        try:
            msg_data = json.loads(message)
            target = msg_data.get("target")
            
            # Treat empty string same as None (broadcast to all clients)
            if target and target in cls.clients:
                # Send to specific client
                _ = cls.clients[target].write_message(message)
            elif target is None or target == "":
                # Send to all clients
                for client in cls.clients.values():
                    _ = client.write_message(message)
            # If target specified but not found, message is silently dropped
        except (json.JSONDecodeError, AttributeError):
            # If message isn't JSON, send to all clients
            for client in cls.clients.values():
                _ = client.write_message(message)
