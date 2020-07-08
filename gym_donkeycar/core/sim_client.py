'''
author: Tawn Kramer
date: 9 Dec 2019
file: sim_client.py
notes: wraps a tcp socket client with a handler to talk to the unity donkey simulator
'''
import json
from .client import SDClient
from .message import IMesgHandler
import time

class SimClient(SDClient):
    """
      Handles messages from a single TCP client.
    """

    def __init__(self, address, msg_handler):
        # we expect an IMesgHandler derived handler
        # assert issubclass(msg_handler, IMesgHandler)
                
        # hold onto the handler
        self.msg_handler = msg_handler

        # connect to sim
        super().__init__(*address)

        # list for holding telemetry positions
        self.positions = []

        # we connect right away
        msg_handler.on_connect(self)

    def send_now(self, msg):
        # takes a dict input msg, converts to json string
        # and sends immediately. right now, no queue.
        json_msg = json.dumps(msg)
        super().send_now(json_msg)

    def queue_message(self, msg):
        # takes a dict input msg, converts to json string
        # and adds to a lossy queue that sends only the last msg
        json_msg = json.dumps(msg)
        self.send(json_msg)

    def on_msg_recv(self, jsonObj):
        # pass message on to handler
        msg_type = self.msg_handler.on_recv_message(jsonObj)
        if msg_type == 'telemetry':
            self.save_telemetry_data(self.msg_handler.get_telemetry())

    # TODO: only record if position changed?? without time, it would not
    # capture when the car is waiting
    def save_telemetry_data(self, telemetry_data):
        # store only the x and z coordinates and speed. y is the vertical data
        position = [telemetry_data["x"], telemetry_data["z"], telemetry_data["speed"]]
        self.positions.append(position)

    def write_telemetry_data(self, fileName="coords.aprfile"):
        with open(fileName, "w") as f:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            f.write("coordinates file created at {}\n".format(current_time))
            f.write("x_pos\ty_pos\tspeed\n")

            for pos in self.positions:
                f.write("{:.4f}\t{:.4f}\t{:.4f}\n".format(pos[0], pos[1], pos[2]))
            print("Finished writing telemetry data to {}".format(fileName))
        
    def is_connected(self):
        return not self.aborted

    def __del__(self):
        self.close()

    def close(self):
        # write out telemetry data at the end
        self.write_telemetry_data()
        # Called to close client connection
        self.stop()

        if self.msg_handler:
            self.msg_handler.on_close()
