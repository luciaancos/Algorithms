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

    # Messages related to the game
    GAME_OK = 5
    MOVE = 6
    INVALID_STATE = 7
    FINNISH = 8


@dataclass
class Message:
    msg_type: MessageType
    _payload: Optional[dict[Any, Any]] = None

    def to_bytes(self) -> bytes:
        if self._payload is not None:
            payload = json.dumps(self._payload).encode()
            return struct.pack(HEADER_FORMAT, self.msg_type.value, len(payload)) + payload
        else:
            return struct.pack(HEADER_FORMAT, self.msg_type.value, 0)

    def is_game_message(self):
        """ Return true if this is a message type that should be exchange
        when a player is in a game """

        return self.msg_type.value >= 6 and self.msg_type.value <= 8

    @property
    def payload(self) -> dict[Any, Any]:
        if self._payload is not None:
            return self._payload
        raise ValueError(f"{self.msg_type.name} does not have a payload")


class StreamSocket:

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer
        host, port = writer.get_extra_info("peername")
        self.peername = f"{host}:{port}"

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

        if length != 0:
            payload_bytes = await self._recv_exact(length)
            if payload_bytes == b"":
                return None

            # TODO: this raises an exception if the decoded string is not valid json
            payload = json.loads(payload_bytes)
        else:
            payload = None

        return Message(MessageType(msg_type), payload)

    async def close(self):
        """ Closes the underlying writer """

        self.writer.close()
        await self.writer.wait_closed()

    async def _recv_exact(self, num: int) -> bytes:
        """ Read exactly num bytes. If the client disconnects, it returns the empty byte string """

        try:
            return await self.reader.readexactly(num)
        except IncompleteReadError as exc:
            if exc.partial == b"":
                return b""
            raise exc
