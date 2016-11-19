import logging
import websockets
import asyncio
import time
import json
from can.can2cane.CaneMessage import CaneMessage
from can.bus import BusABC
from can.message import Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WSBus(BusABC):
    """ Adds support for Cane protocol (CAN over websocket) """

    def __init__(self, channel, *args, **kwargs):
        self.loop = asyncio.new_event_loop()
        self.socket = self.loop.run_until_complete(websockets.connect(kwargs['url'], loop=self.loop, timeout=0))

    def recv(self, timeout=None):
        data = self.loop.run_until_complete(self.socket.recv())
        message = self.deserialize_message(data)
        return message

    def send(self, message):
        message.timestamp = time.time()
        data = self.serialize_message(message)
        self.loop.run_until_complete(self.socket.send(data))

    def deserialize_message(self, data):
        msg = json.loads(data)
        return CaneMessage.decode(msg).can_message

    def serialize_message(self, message):
        msg = CaneMessage.from_can_message(message).encoded
        return json.dumps(msg)

    def shutdown(self):
        self.loop.run_until_complete(self.socket.close())
        self.loop.close()
