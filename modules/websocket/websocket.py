# Tornado websocket for UI communication
# This is PURELY a pass through of data for connectivity. No format conversion is done here.
# Incoming information comes from telemetry_json_output from telemetry
# Outputs information to connected websocket clients
#
# Authors:
# Thomas Selwyn (Devil)

import json
from multiprocessing import Queue, Process
from abc import ABC
from typing import Optional
import logging

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

ws_commands_queue = Queue


class WebSocketHandler(Process):

    """Handles starting the websocket server process."""

    def __init__(self, telemetry_json_output: Queue, ws_commands: Queue):
        super().__init__()
        global ws_commands_queue

        self.telemetry_json_output = telemetry_json_output
        ws_commands_queue = ws_commands

        # Default to test mode
        # ws_commands_queue.put("serial rn2483_radio connect test")

        self.start_websocket_server()

    def start_websocket_server(self) -> None:

        """Starts up the websocket server."""

        wss = tornado.web.Application(
            [(r"/websocket", TornadoWSServer)],
            websocket_ping_interval=10,
            websocket_ping_timeout=30,
        )

        wss.listen(33845)

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

    clients: set = set()
    last_msg_send = {}  # TODO is this supposed to be dict or a string
    global ws_commands_queue

    def open(self) -> None:
        TornadoWSServer.clients.add(self)
        self.send_message(self.last_msg_send)
        logging.info(f"WebSocket: Client connected")

    def on_close(self) -> None:
        TornadoWSServer.clients.remove(self)
        logging.info(f"WebSocket: Client disconnected")

    def on_message(self, message: str) -> None:
        ws_commands_queue.put(message)

    # TODO what does this do and why is origin unused?
    def check_origin(self, origin) -> bool:
        return True

    @classmethod
    def send_message(cls, message: str) -> None:

        if message == "null":
            return

        cls.last_msg_send = message
        for client in cls.clients:
            client.write_message(message)
