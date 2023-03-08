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

from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from dataclasses import dataclass
import struct
import json

if TYPE_CHECKING:
    import socket


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

def recv_from_socket_exact(socket: socket.socket, length: int) -> Optional[bytes]:
    data = b""
    while len(data) != length:
        new_data = socket.recv(length - len(data))
        if new_data == b"":
            return None
        data += new_data
    return data

def recv_from_socket(socket: socket.socket) -> Optional[Message]:
    header = recv_from_socket_exact(socket, HEADER_LEN)
    if header is None:
        return None
    msg_type, length = struct.unpack(HEADER_FORMAT, header)

    payload = recv_from_socket_exact(socket, length)
    if payload is None:
        return None

    return Message(MessageType(msg_type), json.loads(payload))
