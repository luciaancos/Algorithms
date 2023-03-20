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
        logger.info(f"Player connected from '{player.socket.peername}'")

        # TODO: socket.recv_msg() may fail
        # TODO: the base class of all connection related issues is ConnectionError
        # (https://docs.python.org/3/library/exceptions.html#ConnectionError). Handle that exception
        while (msg := await player.socket.recv_msg()) is not None:
            if (game := self.game_manager.get_active_game(player)) is not None:
                if msg.is_game_message():
                    await game.forward_msg(msg, player)
                    if game.has_finished():
                        # TODO: save the state in the database or do whatever is needed after a game has finished
                        pass
                else:
                    await player.socket.send_msg(Message(MessageType.ERROR, {
                        "msg": f"You cannot send a message '{msg.msg_type.value}' while you are playing"
                    }))
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
                logger.info(
                    f"The player '{player.socket.peername}' has created the game '{game_code}'")

            case MessageType.JOIN_GAME:
                game_code = msg.payload["game_code"]
                opponent_player = self.game_manager.get_waiting_player(
                    game_code)

                # Check that the code received makes sense
                if opponent_player is None:
                    await player.socket.send_msg(
                        Message(MessageType.ERROR, {
                                "msg": "No game found for the code '{game_code}'"})
                    )
                    return
                elif opponent_player is player:
                    await player.socket.send_msg(
                        Message(MessageType.ERROR, {
                                "msg": "You cannot join a game if you are also waiting for it"})
                    )
                    return

                game = Game(player, opponent_player)
                self.game_manager.add_new_game(game)
                await game.send_initial_msg()

                self.game_manager.invalidate_code(game_code)

                logger.info(
                    f"'{player.socket.peername}' and '{opponent_player.socket.peername}' have started playing")

    async def on_disconnect(self, player: Player):
        # TODO: do whatever is needed to leave the server in a consistent state:
        #  - When a player which waiting disconnects
        #  - When a player which is playing disconnects
        logger.debug(f"Player '{player.socket.peername}' has disconnected")
        await player.socket.close()
