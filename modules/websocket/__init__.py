import random

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options

import os
import time
import multiprocessing
from modules import serial
import json


class WebSocketServer(tornado.websocket.WebSocketHandler):
    clients = set()

    def open(self):
        WebSocketServer.clients.add(self)
        print(self.request)

    def on_close(self):
        WebSocketServer.clients.remove(self)

    def on_message(self, message):
        print(f"R<<< {message}")

    def check_origin(self, origin):
        return True

    @classmethod
    def send_message(cls, message: str):
        for client in cls.clients:
            print(f"S>>> {message}")
            client.write_message(message)


def random_number():
    return int(random.uniform(0, 1000))


def start():
    print("Tornado Socket Created")
    websocket = tornado.web.Application(
        [(r"/websocket", WebSocketServer)],
        websocket_ping_interval=10,
        websocket_ping_timeout=30,
    )
    websocket.listen(33845)

    io_loop = tornado.ioloop.IOLoop.current()

    periodic_callback = tornado.ioloop.PeriodicCallback(
        lambda: WebSocketServer.send_message(str(random_number())), 1500
    )

    periodic_callback.start()

    io_loop.start()
