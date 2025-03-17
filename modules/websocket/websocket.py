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
import hashlib
import logging
import os.path
import tornado.gen
import tornado.httpserver
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
            _ = wss.listen(33845)
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

    clients: set[TornadoWSServer] = set()
    last_msg_send: str = ""
    pw = "d916d328c73327336b8ccb25a1309a9766df1131f3a5064473933d6aae617442"
    sudo_user = None
    global ws_commands_queue

    def open(self) -> None:
        TornadoWSServer.clients.add(self)
        self.send_message(self.last_msg_send)
        logger.info("Client connected")

    def on_close(self) -> None:
        TornadoWSServer.clients.remove(self)
        logger.info("Client disconnected")

    def on_message(self, message: str) -> None:
        global ws_commands_queue
        logger.info(self)
        if self == TornadoWSServer.sudo_user:
            ws_commands_queue.put(message)
        else:
            msg = message.split(" ")
            if len(msg) != 2: return
            if msg[0] == "auth":
                h = hashlib.sha256()
                h.update(msg[1].encode())
                logger.info(h.hexdigest() == TornadoWSServer.pw)
                if h.hexdigest() == TornadoWSServer.pw:
                    TornadoWSServer.sudo_user = self


    def check_origin(self, _) -> bool:
        """Authenticates clients from any host origin (_ parameter)."""
        return True

    @classmethod
    def send_message(cls, message: str | None) -> None:
        if message is None or message == "null":
            return

        cls.last_msg_send = message
        for client in cls.clients:
            _ = client.write_message(message)
