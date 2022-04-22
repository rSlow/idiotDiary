from games.thousand import GameThousand
from games import BaseGame


class GamesContainer:
    def __init__(self):
        self.games_classes = [GameThousand,
                              ]

    def find_by_name(self, name):
        for game in self.games_classes:
            if game.name == name:
                return game

    @property
    def list_games(self):
        return [game.name for game in self.games_classes]


class GameRooms:
    def __init__(self, game):
        self.game = game
        self.rooms = []
