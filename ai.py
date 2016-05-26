#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
#
# Pure random A.I, you may NOT use it to win ;-)
#
########################################################################
import json
import random
import numpy
import mapConverter
from collections import deque
from mapConverter import MapConverter
from game import Game
import convNet
import math

EXAMPLE_MAP_SIZE = 16
UI_FORMATTING_STRING = "%0.3f"
EXPLORATION_PROBABILITY = 0.7

class AI:
    """Pure random A.I, you may NOT use it to win ;-)"""
    def __init__(self):
        self.net = convNet.ConvNet()
        self.net_move_probability = 0.7
        self.transitions = deque()
        self.reward = 0
        self.prev_state = None
        self._dirs = ["North", "East", "South", "West", "Stay"]
        random.seed()

    def process(self, game):
        """Do whatever you need with the Game object game"""
        self.game = game
        map = MapConverter.convertMap(self.game)
        self.state = self.pad_map(map)

    @staticmethod
    def pad_map(state):
        # state = numpy.random.random_integers(0, 5, (self.game.board_size, self.game.board_size, 2))
        shape = state.shape
        top_pad = int(math.ceil(float(-shape[0] + convNet.MAX_MAP_SIZE) / 2))
        bottom_pad = int(math.floor(float(-shape[0] + convNet.MAX_MAP_SIZE) / 2))
        left_pad = int(math.ceil(float(-shape[1] + convNet.MAX_MAP_SIZE) / 2))
        right_pad = int(math.floor(float(-shape[1] + convNet.MAX_MAP_SIZE) / 2))
        state = numpy.lib.pad(state, ((top_pad, bottom_pad), (left_pad, right_pad), (0, 0)), 'constant',
                              constant_values=mapConverter.TERRAIN)
        return state

    def decide(self):
        """Must return a tuple containing in that order:
          1 - path_to_goal :
                  A list of coordinates representing the path to your
                 bot's goal for this turn:
                 - i.e: [(y, x) , (y, x), (y, x)]
                 where y is the vertical position from top and x the
                 horizontal position from left.

          2 - action:
                 A string that will be displayed in the 'Action' place.
                 - i.e: "Go to mine"

          3 - decision:
                 A list of tuples containing what would be useful to understand
                 the choice you're bot has made and that will be printed
                 at the 'Decision' place.

          4- hero_move:
                 A string in one of the following: West, East, North,
                 South, Stay

          5 - nearest_enemy_pos:
                 A tuple containing the nearest enenmy position (see above)

          6 - nearest_mine_pos:
                 A tuple containing the nearest enenmy position (see above)

          7 - nearest_tavern_pos:
                 A tuple containing the nearest enenmy position (see above)"""

        forced_exploration = random.uniform(0.0, 1.0) < EXPLORATION_PROBABILITY

        path_to_goal = []
        first_cell = self.game.hero.pos
        path_to_goal.append(first_cell)

        dirWeights = self.net.calculateDecisions(self.state)
        decision = [
            ("North", UI_FORMATTING_STRING % dirWeights[0]),
            ("East", UI_FORMATTING_STRING % dirWeights[1]),
            ("South", UI_FORMATTING_STRING % dirWeights[2]),
            ("West", UI_FORMATTING_STRING % dirWeights[3]),
            ("Stay", UI_FORMATTING_STRING % dirWeights[4])
        ]

        if len(self.transitions) < convNet.TRAINING_BATCH_SIZE or forced_exploration:
            self.hero_move = random.choice(self._dirs)
        else:
            self.hero_move = self._dirs[dirWeights.argmax(0)]

        nearest_enemy_pos = (0, 0)   # random.choice(self.game.heroes).pos
        nearest_mine_pos = (0, 0)    # random.choice(self.game.mines_locs)
        nearest_tavern_pos = (0, 0)  # random.choice(self.game.mines_locs)

        return (path_to_goal,
                "explore" if forced_exploration else "",
                decision,
                self.hero_move,
                nearest_enemy_pos,
                nearest_mine_pos,
                nearest_tavern_pos)

    def _save_transition(self):
        if not (self.prev_state is None):
            transition = (self.prev_state, self.prev_action, self.reward, self.state)
            self.transitions.append(transition)

    def post_process(self):
        self.reward = self._calculate_reward()
        self._save_transition()
        self.prev_state = self.state
        self.prev_action = numpy.zeros(len(self._dirs))
        self.prev_action[self._dirs.index(self.hero_move)] = 1

        if len(self.transitions) > convNet.TRAINING_BATCH_SIZE:
            self.net.trainNetwork(self.transitions)

    def _calculate_reward(self):
        return self.game.hero.gold - self.reward

if __name__ == "__main__":
    with open('exampleMap.json') as data_file:
        data = json.load(data_file)
    gameobj = Game(data)

    ai = AI()
    for i in range(250):
        ai.process(gameobj)
        ai.decide()
        ai.post_process()
        print("%d ---" % i)

