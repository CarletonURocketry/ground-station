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

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

ws_commands_queue = Queue


class WebSocketHandler(Process):
    def __init__(self, telemetry_json_output: Queue, ws_commands: Queue):
        super().__init__()
        global ws_commands_queue

        self.telemetry_json_output = telemetry_json_output
        ws_commands_queue = ws_commands

        # Default to test mode
        # ws_commands_queue.put("serial rn2483_radio connect test")

        self.start_websocket_server()

    def start_websocket_server(self):
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

    def check_for_messages(self):
        json_data = None
        while not self.telemetry_json_output.empty():
            json_data = self.telemetry_json_output.get()
        return json.dumps(json_data)


class TornadoWSServer(tornado.websocket.WebSocketHandler, ABC):
    clients = set()
    last_msg_send = {}
    global ws_commands_queue

    def open(self):
        TornadoWSServer.clients.add(self)
        self.send_message(self.last_msg_send)
        print(f"WebSocket: Client connected")

    def on_close(self):
        TornadoWSServer.clients.remove(self)
        print(f"WebSocket: Client disconnected")

    def on_message(self, message):
        ws_commands_queue.put(message)

    def check_origin(self, origin):
        return True

    @classmethod
    def send_message(cls, message: str):
        if message != "null":
            cls.last_msg_send = message
            for client in cls.clients:
                client.write_message(message)
