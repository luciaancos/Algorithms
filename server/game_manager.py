from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import secrets
import random
import logging

from packet import Message, MessageType


if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger(__name__)


class Game:
    """ Stores the state of a game """

    def __init__(self,
                 first_player: Player, second_player: Player, *,
                 preserve_order=False,
                 turn=Optional[int]):
        """ 'first_players' and 'second_players' are the users which are playing a
        game. If preserve_order is True, then 'first_user' moves the white pieces 
        and 'second_user' moves the black ones. Otherwise, this decision is taken
        randomly """

        # This should be checked after a message is forwarded
        self.has_finished = False

        if turn is None or turn not in (0, 1):
            self._turn = random.randint(0, 1)
        else:
            self._turn = turn

        if preserve_order:
            self.white_player = first_player
            self.black_player = second_player
        else:
            self.white_player = first_player if random.random() < 0.5 else second_player
            self.black_player = first_player if self.white_player is second_player else second_player

    async def send_initial_msg(self):
        """ Sends the initial message to both players """

        # The initial state is not needed if the board starts in that state
        # TODO: the fact that 0 is associated with the white player and 1 is associated
        # with the black player should be obtain from the module which encodes the game logic

        await self.white_player.socket.send_msg(
            Message(MessageType.GAME_OK,
                    {"assigned_turn": 0, "start_turn": self._turn}
            ))

        await self.black_player.socket.send_msg(
                Message(MessageType.GAME_OK, 
                    {"assigned_turn": 1, "start_turn": self._turn}
        ))

    async def forward_msg(self, msg: Message, player: Player):
        """ Sends the given message to the opponent_player of 'player'. If player is not actually
        playing in this game, raise an exception """

    def is_white(self, player: Player) -> bool:
        """ Returns true if the given player is the white player """

        return player.socket.peername == self.white_player.socket.peername

    def is_black(self, player: Player):
        """ Returns true if the given player is the black player """

        return player.socket.peername == self.black_player.socket.peername


class GameManager:

    def __init__(self):
        self._wait_dict = {}
        # Maps a players 'ip:port' to the current game they are playing
        self._player_to_game = {}

    def add_to_waitlist(self, player: Player) -> str:
        """ Add the given player to a waitlist and return a game code which will be used
        to join that game """

        while (game_code := secrets.token_hex(8)) in self._wait_dict:
            pass

        self._wait_dict[game_code] = player
        return game_code

    def get_waiting_player(self, code: str) -> Optional[Player]:
        """ Check whether the given code exists """

        return self._wait_dict.get(code)

    def add_new_game(self, game: Game):
        """ Adds a new game.
        NOTE: it does not check if the players are in another game """

        white_id, black_id = (game.white_player.socket.peername,
                              game.black_player.socket.peername)

        self._player_to_game[white_id] = game
        self._player_to_game[black_id] = game

    def invalidate_code(self, code: str):
        """ Remove the given code. If the code does not exist, it raises an exception """

        del self._wait_dict[code]

    def delete_game(self, player: Player):
        """ Deletes the game where 'player' is playing. A player can only play in one game
        so there does not exist any ambiguity """

        if (game := self.get_active_game(player)) is None:
            raise RuntimeError(
                f"The player '{player.socket.peername}' is not playing any game")

        white_id, black_id = (game.white_player.socket.peername,
                              game.black_player.socket.peername)

        del self._player_to_game[white_id]
        del self._player_to_game[black_id]

    def get_active_game(self, player: Player) -> Optional[Game]:
        """ Returns an active game where the given player is playing """

        return self._player_to_game.get(player.socket.peername)
