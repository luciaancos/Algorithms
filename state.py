from __future__ import annotations
import copy
from dataclasses import dataclass
from game import GameMode, InvalidMoveException, InvalidStateException, MillGame, CellState


@dataclass
class Move: 
    pos_init: int
    next_pos: int
    kill: int

    def __str__(self) -> str:
        return f"<move>={{'POS_INIT':{self.pos_init}, 'NEXT_POS':{self.next_pos},'KILL':{self.kill}}}"

@dataclass
class Sucesor:
    state : State
    move: Move
    next_state: State

    def __str__(self) -> str:
        return f"<sucesor>={{'STATE':{self.state},'MOVE':{self.move},'NEXT_STATE':{self.next_state}}}"
@dataclass
class Action:
    move: Move
    sucesor: Sucesor

    def __str__(self) -> str:
        return f"{self.move}, {self.sucesor}"

class State:
    
    def __init__(self,
                 game: MillGame):
        self.game = game
        self.free = [] 
        self.gamer = [[],[]]
        self.turn = game.turn
        self.chips = []

        for i in range(24):
            if self.game.board.buff[i] == CellState.EMPTY:
                self.free.append(i)

        auxW = []
        for i in range(24):
            if self.game.board.buff[i] == CellState.WHITE:
                auxW.append(i)
        self.gamer[0] = auxW
        auxB = []
        for i in range(24):
            if self.game.board.buff[i] == CellState.BLACK:
                auxB.append(i)
        self.gamer[1] = auxB

        self.chips.append(self.game._players[0].remaining_pieces)
        self.chips.append(self.game._players[1].remaining_pieces)

    def generate_succ_place(self, successors: list[Action]) -> list[Action]:
        for free_chip in self.free:
            game_copy = copy.deepcopy(self.game)
            try:
                game_copy.place(free_chip//8,free_chip%8)
            except(ValueError, InvalidMoveException, InvalidStateException):
                continue
            
            if game_copy.has_to_delete:
                for opponent_chip in self.gamer[self.turn.value]:
                    try:
                        game_copy.remove(opponent_chip//8, opponent_chip%8)
                    except(ValueError, InvalidMoveException, InvalidStateException):
                        continue
                    next_state = State(game_copy)
                    move = Move(-1,free_chip, opponent_chip)
                    sucessor = Sucesor(self, move,next_state)
                    action = Action(move, sucessor)
                    successors.append(action)
            else:
                next_state = State(game_copy)
                move = Move(-1,free_chip, -1)           
                sucessor = Sucesor(self, move,next_state)
                action = Action(move, sucessor)
                successors.append(action)
        return successors

    def generate_succ_move(self, successors: list[Action]) -> list[Action]:
        for player_chip in self.gamer[1 - self.turn.value]:
                for free_chip in self.free:
                    game_copy = copy.deepcopy(self.game)
                    try:
                        game_copy.move(player_chip//8,player_chip%8,free_chip//8,free_chip%8)
                    except(ValueError, InvalidMoveException, InvalidStateException):
                        continue
                    if game_copy.has_to_delete:
                        for opponent_chip in self.chips[self.turn.value]:
                            try:
                                game_copy.remove(opponent_chip//8, opponent_chip%8)
                            except(ValueError, InvalidMoveException, InvalidStateException):
                                continue
                            next_state = State(game_copy)
                            move = Move(player_chip,free_chip, opponent_chip)
                            sucessor = Sucesor(self, move, next_state)
                            action = Action(move, sucessor)
                            successors.append(action)
                    else:
                        next_state = State(game_copy)
                        move = Move(player_chip,free_chip, -1)                     
                        sucessor = Sucesor(self, move, next_state)
                        action = Action(move, sucessor)
                        successors.append(action)


    def successors(self) -> list[Action]:
        successors = []
        
        if self.game.mode == GameMode.PLACE:
            successors = self.generate_succ_place(successors)
                                
        if self.game.mode == GameMode.MOVE:
            successors = self.generate_succ_move(successors)
    
        return successors

    def __str__(self) -> str:
        joined_free = ",".join(map(str, self.free))
        joined_gamers = ",".join(map(str, self.gamer))
        joined_chips = ",".join(map(str, self.chips))
        return f"<state>={{'FREE':[ {joined_free} ],'GAMER':[{joined_gamers}],'TURN':{self.turn.name},'CHIPS':{joined_chips}}}"