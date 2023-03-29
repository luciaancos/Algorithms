from __future__ import annotations
from cmath import sqrt
import math
from typing import Optional
from state import State
from game import GameMode


class MontecarloNode:
    def __init__(self, state: State, parent: Optional[MontecarloNode]):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.won_plays = 0
        self.lost_plays = 0
        self._sucessors = self.state.successors(shuffle=True)

    def next_child(self):
        try:
            new_state = next(self._sucessors)
            child = MontecarloNode(new_state, self)
            self.children.append(child)
            return new_state 
        except StopIteration:
            return None
        

    def get_evaluation(self):
        if self.parent is None:
            raise ValueError("You can not get the evaluation of the root")
        return (self.won_plays - self.lost_plays)/self.visits+2/sqrt(2)*sqrt(2*math.log(self.parent.visits)/self.visits)

    def get_best_child(self):
        return max([(child.get_evaluation(), child) for child in self.children])[1]

    def is_terminal(self):
        return self.state.game.mode == GameMode.FINISHED

    

