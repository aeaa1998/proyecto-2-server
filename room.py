from client import Client
from deck import Deck
import uuid
import random
import json


class RoomEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "room",
            '__room__': {
                'id': o.id,
                'deck': o.deck,
            },
        }


class Room(object):
    def __init__(self):
        self.id = uuid.uuid4().hex
        self.deck = Deck()
        self.visible_deck = Deck([], False)
        self.clients = []
        self.started = False
        self.dealer = None
        self.reset_count = 0

    def add_client(self, username, conn):
        client_to_add = Client(self.id, username, len(self.clients) + 1, conn)
        self.clients.append(
            client_to_add
        )
        return client_to_add

    def start_game(self):
        self.started = True

    def reset_room(self):
        for client in self.clients:
            client.lives = 4
            self.visible_deck.reset_cards()
            self.deck.reset_cards()
            self.reset_count = 0

    def remove_client(self, username):
        for client in self.clients:
            if client.username == username:
                self.clients.remove(client)
                return

    def set_dealer(self):
        self.dealer = random.choice(self.clients)
