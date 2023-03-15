from __future__ import annotations

import logging
import asyncio
from typing import TYPE_CHECKING

from packet import Message, MessageType, StreamSocket
from game_manager import Game, GameManager
from player import Player

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter

    from packet import Message


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

        player = Player(StreamSocket(reader, writer))
        logger.info(f"User connected from '{player.socket.peername}'")

        # TODO: socket.recv_msg() may fail
        while (msg := await player.socket.recv_msg()) is not None:
            if (game := self.game_manager.get_active_game(player)) is not None:
                await self.handle_game_msg(game, player, msg)
            else:
                await self.handle_msg(player, msg)

        await self.on_disconnect(player)

    async def handle_msg(self, player: Player, msg: Message):
        match msg.msg_type:
            case MessageType.CREATE_GAME:
                # TODO: check that the player is not already waiting to join a game
                game_code = self.game_manager.add_to_waitlist(player)
                await player.socket.send_msg(Message(MessageType.OK, {
                    "game_code": game_code
                }))

    async def handle_game_msg(self, game: Game, player: Player, msg: Message):
        pass

    async def on_disconnect(self, player: Player):
        # TODO: do whatever is needed to leave the server in consistent state:
        #  - When a player which waiting disconnects
        #  - When a player which is playing disconnects
        logger.debug(f"User '{player.socket.peername}' has disconnected")
        await player.socket.close()
