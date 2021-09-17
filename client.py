import json

class ClientEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "client",
            '__client__': {
                "lives": o.lives,
                "cards": [card.dump() for card in o.cards],
                "is_dealer": o.is_dealer
            }
        }

ClientCanPullCard = {
            '__type__': "client_card_pull_allowed",
        }

class ClientReviveEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "client_revive",
            'lives': 1
        }

class ClientLostLifeEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "client_lost",
            'lives': o.lives
        }

class ClientSavedEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "client_saved",
        }

class ClientDiedEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "client_died",
        }

class Client(object):
    def __init__(self, room_id, username, order, connection):
        self.username = username
        self.order = order
        self.room_id = room_id
        self.connection = connection
        self.lives = 4
        self.is_dealer = False
        self.cards = []
        self.hand = None

    def reset(self, with_lives = True):
        self.cards = []
        if with_lives:
            self.lives = 4
        self.is_dealer = False
        self.hand = None

    def discard_card(self, _card):
        for card in self.cards:
            if card.letter == _card.letter and card.type == _card.type:
                self.cards.remove(card)
    
    def add_card(self, card):
        self.cards.append(card)

    def send(self, message):
        self.connection.send(message)

    def send_prescence(self):
        client_dump = self.dump()
        self.connection.send(client_dump)

    def send_life_prescence(self, encoder):
        dump = json.dumps(self, indent=4, cls=encoder)
        self.connection.send(dump)

    def send_can_pull_card(self):
        dump = json.dumps(ClientCanPullCard, indent=4)
        self.connection.send(dump)

    def dump(self):
        return json.dumps(self, indent=4, cls=ClientEncoder)
