import logging
import websockets
import asyncio
import time
import json
import threading
from can.can2cane.CaneMessage import CaneMessage
from can.bus import BusABC
from can.message import Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WSBus(BusABC):
    """ Adds support for Cane protocol (CAN over websocket) """

    def __init__(self, channel, *args, **kwargs):
        self.url = kwargs['url']
        self.socket = None
        # start the loop
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever)
        self.thread.start()
        # connect
        asyncio.run_coroutine_threadsafe(self.ensure_connected(), self.loop).result()

    async def ensure_connected(self):
        while self.socket is None or self.socket.open == False:
            try:
                self.socket = await websockets.connect(self.url, loop=self.loop, timeout=0)
            except:
                print('Could not connect, reconnectig ...')
                time.sleep(1)

    async def recv_io(self):
        await self.ensure_connected()
        return await self.socket.recv()

    async def send_io(self, data):
        await self.ensure_connected()
        return await self.socket.send(data)

    def recv(self, timeout=None):
        future = asyncio.run_coroutine_threadsafe(self.recv_io(), self.loop)
        data = future.result(timeout)
        message = self.deserialize_message(data)
        return message

    def send(self, message):
        message.timestamp = time.time()
        data = self.serialize_message(message)
        return asyncio.run_coroutine_threadsafe(self.send_io(data), self.loop).result()

    def deserialize_message(self, data):
        msg = json.loads(data)
        return CaneMessage.decode(msg).can_message

    def serialize_message(self, message):
        msg = CaneMessage.from_can_message(message).encoded
        return json.dumps(msg)

    def shutdown(self):
        future = asyncio.run_coroutine_threadsafe(self.socket.close(), self.loop)
        future.result()
        self.loop.call_soon_threadsafe(self.loop.stop)
