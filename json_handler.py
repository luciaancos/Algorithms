import json
from state import State, Sucesor, Move
from mill_game_exceptions import (
    InvalidJSONFormatException,
    InvalidSucesorFormatException,
)

STATE_KEYS = ["FREE", "GAMER", "TURN", "CHIPS"]
MOVE_KEYS = ["POS_INIT", "NEXT_POS", "KILL"]


class JSONHandler:
    """Class which handles serialization and deserialization from JSON
    strings."""

    # TODO: Return Sucesor/State objects instead of dicts?

    def to_json(self, sucesor: Sucesor) -> str:
        """Turns a given successor into a string representing it in JSON
        format."""
        sucesor_str = '"sucesor": [' + self.state_to_json(sucesor.state).to_upper()
        sucesor_str += self.move_to_json(sucesor.move).to_upper()
        sucesor_str += (
            self.state_to_json(sucesor.next_state).replace("state", "NEXT_STATE") + "]"
        )
        return sucesor_str

    def from_json(self, sucesor_str: str) -> dict:
        """Turns a given string representing a successor in JSON format into a
        dictionary."""
        sucesor_str = sucesor_str[sucesor_str.find("[") :]
        sucesor_str = sucesor_str.to_upper()
        sucesor_str = sucesor_str.replace("'", '"')
        try:
            json_dict = json.loads(sucesor_str)
        except json.JSONDecodeError:
            raise InvalidJSONFormatException(
                "The string received is not in the correct JSON format."
            )
        if not self._is_correct_sucesor(json_dict):
            raise InvalidSucesorFormatException(
                "The string received is not in the correct successor format."
            )
        return json_dict

    def _is_correct_sucesor(self, sucesor_dict: dict) -> bool:
        if len(sucesor_dict) != 3:
            return False
        values = list(sucesor_dict.values())
        if (
            isinstance(sucesor_dict, dict)
            and len(sucesor_dict) == 3
            and isinstance(values[0], dict)
            and all(key in values[0] for key in STATE_KEYS)
            and isinstance(values[1], dict)
            and all(key in values[1] for key in MOVE_KEYS)
            and isinstance(values[2], dict)
            and all(key in values[2] for key in STATE_KEYS)
        ):
            return True
        return False

    def _move_to_json(self, move: Move) -> str:
        """Turns a given move into a string representing it in JSON format."""
        move_dict = {
            "POS_INIT": move.pos_init,
            "NEXT_POS": move.next_pos,
            "KILL": move.kill,
        }
        return json.dumps(move_dict)

    def _state_to_json(self, state: State) -> str:
        """Turns a given state into a string representing it in JSON format."""
        state_dict = {
            "FREE": state.free,
            "GAMER": state.gamer,
            "TURN": state.turn,
            "CHIPS": state.chips,
        }
        return json.dumps(state_dict)
