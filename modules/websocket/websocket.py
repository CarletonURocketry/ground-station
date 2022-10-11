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
