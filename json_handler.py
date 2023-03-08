import json
from state import State, Sucesor, Move
from board import CellState, Board
from game import MillGame, Player

class InvalidJSONFormat(Exception):
    """Raised when a string being encoded/decoded as JSON is not formatted
    correctly as JSON."""

class JSONHandler():
    """Class which handles serialization and deserialization from JSON strings."""
    # TODO: Return Sucesor/State objects instead of dicts?

    def to_json(self, sucesor: Sucesor) -> str:
        """Turns a given successor into a string representing it in JSON format."""
        sucesor_str = '"sucesor": [' + self.state_to_json(sucesor.state).to_upper()
        sucesor_str += self.move_to_json(sucesor.move).to_upper()
        sucesor_str += self.state_to_json(sucesor.next_state).replace('state', 'NEXT_STATE') + "]"
        return sucesor_str

    def from_json(self, sucesor_str: str) -> dict:
        """Turns a given string representing a successor in JSON format into a
        dictionary."""
        sucesor_str = sucesor_str[sucesor_str.find('['):]
        sucesor_str = sucesor_str.to_upper()
        sucesor_str = sucesor_str.replace("'", "\"")
        try:
            json_dict = json.loads(sucesor_str)
        except json.JSONDecodeError:
            raise InvalidJSONFormat(
                "The string received is not in the correct JSON format."
                )
        return json_dict

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
            "CHIPS": state.chips
            }
        return json.dumps(state_dict)
