""" This module contains utilities related to the network packet format. 

The format is very simple. The first 2 bytes correspond to the message type. The next 4 bytes encodes the length 
in bytes of the json that follows it. This is not the most efficient design but it is very flexible.

2 bytes    4 bytes          LENGTH bytes
------ ------------ ------------------------------
|TYPE | |  LENGTH  | |      JSON payload          |
------ ------------ ------------------------------ 

The bytes are in network order (big-endian) and the json is UTF-8 encoded
"""

from __future__ import annotations
from asyncio.exceptions import IncompleteReadError
import logging

from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from dataclasses import dataclass
import struct
import json

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter


# The size, in bytes, of the length field of the packet
LENGTH_FIELD_LEN = 4

# The size, in bytes, of the type field of the packet
TYPE_FIELD_LEN = 2

HEADER_LEN = LENGTH_FIELD_LEN + TYPE_FIELD_LEN
HEADER_FORMAT = "!HI"

# Constants which represent the type of packages. These are the ones placed in the type field
class MessageType(Enum):
    CREATE_GAME = 1
    JOIN_GAME = 2
    ERROR = 3
    OK = 4

@dataclass
class Message:
    msg_type: MessageType
    payload: dict[Any, Any]

    def to_bytes(self) -> bytes:
        payload = json.dumps(self.payload).encode()

        return struct.pack(HEADER_FORMAT, self.msg_type.value, len(payload)) + payload


class StreamSocket:

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer
        self.peername = writer.get_extra_info("peername")

    async def send_msg(self, msg: Message):
        """ Sends the message via the underlying writer """

        self.writer.write(msg.to_bytes())
        await self.writer.drain()

    async def recv_msg(self) -> Optional[Message]:
        """ Reads exactly one message. The function blocks until a message is read """

        header = await self._recv_exact(HEADER_LEN)
        if header == b"":
            return None

        msg_type, length = struct.unpack(HEADER_FORMAT, header)
        payload = await self._recv_exact(length)
        if payload == b"":
            return None

        return Message(msg_type, json.loads(payload))

    async def _recv_exact(self, num: int) -> bytes:
        """ Read exactly num bytes. If the client disconnects, it returns the empty byte string """

        try:
            return await self.reader.readexactly(num)
        except IncompleteReadError as exc:
            logger.debug(f"Client {self.peername} disconneted. Raised: '{exc}'")
            return b""
