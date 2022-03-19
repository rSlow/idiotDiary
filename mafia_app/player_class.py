import mafia_app.user_classes as roles
roles.

class Player:
    def __init__(self, name,
                 role=roles.Civilian()):
        self.name = name
        self.role = role

        self.live_status = True
        self.in_game_status = True

        self.talk_status = True
        self.previous_involved = None
        self.self_action = None
