import tornado
import tornado.web
import tornado.httpserver
import tornado.ioloop

from modules.websocket.websocket import WebSocketServer, random_number


def start():
    print("Tornado Socket Created")
    wss = tornado.web.Application(
        [(r"/websocket", WebSocketServer)],
        websocket_ping_interval=10,
        websocket_ping_timeout=30,
    )
    wss.listen(33845)

    io_loop = tornado.ioloop.IOLoop.current()

    periodic_callback = tornado.ioloop.PeriodicCallback(
        lambda: WebSocketServer.send_message(str(random_number())), 1500
    )

    periodic_callback.start()

    io_loop.start()
