import os
import time
from _thread import *
import threading

from modules import websocket, serial
import multiprocessing
import json


input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()


def main():
    cls = lambda: os.system('cls' if os.name == 'nt' else 'clear')
    printCURocket("Not a missile", "lethal", "POWERED ASCENT")

    # i = 0
    # while True:
    # i = i + 1
    # cls()
    # printCURocket("Not a missile", f"lethal {i}", "POWERED ASCENT")
    # time.sleep(1)

    # Initialize serial connection to board
    #serial.main()
    # Initialize Tornado websocket for UI communication
    websocket.start()



def printCURocket(callsign, version, status):
    print(fr"""
           ^
          / \
         /___\
        |=   =|
        |     |
        | C U |
        | I N |
        |Space|
        |     |
        |     |
        |     |
       /|##!##|\
      / |##!##| \
     /  |##!##|  \
    |  / ^ | ^ \  |
    | /  ( | )  \ |
    |/   ( | )   \|
        ((   ))
       ((  :  ))            CU InSpace Telemetry Driver
       ((  :  ))            Callsign  {callsign}
        ((   ))             Version   {version}
          ( )               Status    {status}
              """)


if __name__ == '__main__':
    main()
