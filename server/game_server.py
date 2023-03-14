from __future__ import annotations

import logging
import asyncio
from typing import TYPE_CHECKING

from packet import StreamSocket
from game_manager import GameManager

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter


logger = logging.getLogger(__name__)


class GameServer:

    def __init__(self):
        self.game_manager = GameManager()

    async def start_server(self, host: str, port: int):
        server = await asyncio.start_server(self.handle_connection, host, port)

        # TODO: this information should be obtained from the server object. Right?
        logger.debug(f"Running server on {host}:{port}")
        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter):
        # FIXME: exceptions may be ignored inside a task. To handle this, we either await on the
        # task or handle the exception inside of it. In this case, I don't think the exception
        # will get ignored because this happens when we keep a reference for the task and I
        # think that is not done.

        # TODO: should I close the connection if the other end has already done it? 

        socket = StreamSocket(reader, writer)
        logger.info(f"Connection made from {socket.peername}")

        while (msg := await socket.recv_msg()) is not None:
            print(socket.peername, msg)

