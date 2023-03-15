from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import secrets
import random


if TYPE_CHECKING:
    from player import Player

class Game:
    """ Stores the state of a game """

    def __init__(self,
                first_player: Player,
                second_player: Player,
                preserve_order=False):
        """ 'first_players' and 'second_players' are the users which are playing a
        game. If preserve_order is True, then 'first_user' moves the white pieces 
        and 'second_user' moves the black ones. Otherwise, this decision is taken
        randomly """

        if preserve_order:
            self.white_player = first_player
            self.black_player = second_player
        else:
            self.white_player = first_player if random.random() < 0.5 else second_player
            self.black_player = first_player if self.white_player is second_player else second_player


class GameManager:

    def __init__(self):
        self._wait_dict = {}

    def add_to_waitlist(self, player: Player) -> str:
        """ Add the given player to a waitlist and return a game code which will be used
        to join that game """

        while (game_code := secrets.token_hex()) in self._wait_dict:
            pass

        self._wait_dict[game_code] = player
        return game_code

    def get_active_game(self, player: Player) -> Optional[Game]:
        """ Returns an active game where the given player is playing """

        return None
