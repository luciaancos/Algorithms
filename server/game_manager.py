from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import secrets
import random
import logging
import asyncio

from packet import Message, MessageType


if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger(__name__)


class Game:
    """Stores the state of a game"""

    def __init__(
        self,
        first_player: Player,
        second_player: Player,
        *,
        preserve_order=False,
        max_consecutive_errors=6,
        turn=Optional[int],
    ):
        """'first_players' and 'second_players' are the users which are playing a
        game.

        Turn is the player who starts moving. If None is given, then it is chosen
        randomly. This may be changed in the future so that instead of being an integer,
        it is an instance of Turn.

        max_consecutive_errors is the maximum number of INVALID_STATE messages which
        a game can see in a consecutive manner before invalidating the game

        If preserve_order is True, then 'first_user' moves the white pieces
        and 'second_user' moves the black ones. Otherwise, this decision is taken
        randomly
        """

        self.max_consecutive_errors = max_consecutive_errors

        # Number of consecutive FINNISH messages received
        self._finished_cnt = 0
        self._errors_cnt = 0

        # TODO: keep track of the non-error messages which have been exchanged
        # to know when the game has finished because of a tie

        if turn is None or turn not in (0, 1):
            self._turn = random.randint(0, 1)
        else:
            self._turn = turn

        if preserve_order:
            self.white_player = first_player
            self.black_player = second_player
        else:
            self.white_player = first_player if random.random() < 0.5 else second_player
            self.black_player = (
                first_player if self.white_player is second_player else second_player
            )

        # This lock is needed 
        self.lock = asyncio.Lock()
        self._cnts = [0, 0]

    async def send_initial_msg(self):
        """Sends the initial message to both players"""

        # The initial state is not needed if the board starts in that state

        # TODO: the fact that 0 is associated with the white player and 1 is associated
        # with the black player should be obtain from the module which encodes the game logic
        await self.white_player.socket.send_msg(
            Message(MessageType.GAME_OK, {"assigned_turn": 0, "start_turn": self._turn})
        )

        await self.black_player.socket.send_msg(
            Message(MessageType.GAME_OK, {"assigned_turn": 1, "start_turn": self._turn})
        )

    async def forward_msg(self, msg: Message, player: Player):
        """Sends the given message to the opponent_player of 'player'. If the player is not
        playing in this game or 'msg' is a message which is not allowed
        to be sent while the player is playing, an exception is raised."""

        if self.has_finished():
            raise RuntimeError(
                "You are trying to handle a message for a game which has finished"
            )

        if not msg.is_game_message():
            raise ValueError(
                f"{msg.msg_type.value} is not an allowed message when the player is playing"
            )

        if not self.is_playing(player):
            raise ValueError(f"{player.socket.peername} is not playing in the game")

        async with self.lock:
            await self._handle_forward_message(msg, player)


    async def _handle_forward_message(self, msg: Message, player: Player):
        """ This method must be executed in mutual exclusion. Otherwise, the invariants that have to hold
        for the counters won't do it """
        if not self._is_turn(player):
            await player.socket.send_msg(
                Message(
                    MessageType.ERROR,
                    {
                        "msg": "It is not your turn. Wait until the other player performs a move "
                    },
                )
            )
            return

        if self.has_finished():
            await player.socket.send_msg(
                    Message(
                        MessageType.ERROR, 
                        {"msg": "The game has already finished and will be soon be deleted"}
                    )
                )

        opponent_player = self._opponent_player(player)

        match msg.msg_type:
            case MessageType.MOVE:
                self._finished_cnt = 0
                self._cnts[self._turn] = 0
            case MessageType.INVALID_STATE:
                self._finished_cnt = 0
                self._cnts[self._turn] += 1
            case MessageType.FINNISH:
                self._finished_cnt += 1
                self._change_turn()

        # Forward the message if the game has not finished
        if not self.has_finished():
            await opponent_player.socket.send_msg(msg)
            self._change_turn()
        else:
            if not self.max_errors_reached():
                # Then this is the second consecutive FINNISH
                # TODO: change this
                if msg.payload["is_tie"]:
                    turn_value = -1
                else:
                    # If it is not tie, the winner is the first one who sent the message
                    turn_value = 1 - self._turn

                await player.socket.send_msg(Message(MessageType.STATS, {
                    "type": "game_result",
                    "winner": turn_value
                }))
            else:
                await player.socket.send_msg(Message(MessageType.STATS, {
                    "type": "max_error_reached"
                }))

    def has_finished(self) -> bool: 
        """Returns true if this game has finished"""

        return (
            self._finished_cnt == 2 or self.max_errors_reached()
        )

    def max_errors_reached(self) -> bool:
        return (self._cnts[0] == self.max_consecutive_errors or 
                    self._cnts[1] == self.max_consecutive_errors)

    def is_playing(self, player: Player) -> bool:
        """Returns true if the given player is playing in this game"""

        return self._is_white(player) or self._is_black(player)

    def _is_white(self, player: Player) -> bool:
        """Returns true if the given player is the white player. It is assumed that 'player' is
        playing this game"""

        return player.socket.peername == self.white_player.socket.peername

    def _change_turn(self):
        """Changes the turn"""

        self._turn = 1 - self._turn

    def _is_black(self, player: Player) -> bool:
        """Returns true if the given player is the black player. It is assumed that 'player' is
        playing this game"""

        return player.socket.peername == self.black_player.socket.peername

    def _opponent_player(self, player: Player) -> Player:
        """Returns the opponent player of the given player. It is assumed that 'player' is
        playing this game"""

        if self._is_white(player):
            return self.black_player
        return self.white_player

    def _is_turn(self, player: Player) -> bool:
        """Returns true if it is the turn of current_player. It is assumed that 'player' is
        playing this game"""

        return (self._is_black(player) and self._turn == 1) or (
            self._is_white(player) and self._turn == 0
        )


class GameManager:
    def __init__(self):
        self._wait_dict = {}
        # Maps a players 'ip:port' to the current game they are playing
        self._player_to_game = {}

    def add_to_waitlist(self, player: Player) -> str:
        """Add the given player to a waitlist and return a game code which will be used
        to join that game"""

        while (game_code := secrets.token_hex(8)) in self._wait_dict:
            pass

        self._wait_dict[game_code] = player
        return game_code

    def get_waiting_player(self, code: str) -> Optional[Player]:
        """Check whether the given code exists"""

        return self._wait_dict.get(code)

    def add_new_game(self, game: Game):
        """Adds a new game.
        NOTE: it does not check if the players are in another game"""

        white_id, black_id = (
            game.white_player.socket.peername,
            game.black_player.socket.peername,
        )

        self._player_to_game[white_id] = game
        self._player_to_game[black_id] = game

    def invalidate_code(self, code: str):
        """Remove the given code. If the code does not exist, it raises an exception"""

        del self._wait_dict[code]

    def delete_game(self, player: Player):
        """Deletes the game where 'player' is playing. A player can only play in one game
        so there does not exist any ambiguity"""

        if (game := self.get_active_game(player)) is None:
            raise RuntimeError(
                f"The player '{player.socket.peername}' is not playing any game"
            )

        white_id, black_id = (
            game.white_player.socket.peername,
            game.black_player.socket.peername,
        )

        del self._player_to_game[white_id]
        del self._player_to_game[black_id]

    def get_active_game(self, player: Player) -> Optional[Game]:
        """Returns an active game where the given player is playing"""

        return self._player_to_game.get(player.socket.peername)
