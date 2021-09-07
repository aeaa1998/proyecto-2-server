from card import Card
from constants import generate_maze
import random
import json


class DeckDecoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': 'deck',
            '__deck__': {
                'is_visible': o.is_visible
            }
        }


class Deck(object):
    def __init__(self, cards=generate_maze(), is_visible=False):
        self.cards = cards
        self._initial_cards = cards
        self.is_visible = is_visible

    def reset_cards(self):
        self.cards = self._initial_cards.copy()

    @property
    def card_count(self):
        return len(self.cards)

    @property
    def is_empty(self):
        return self.card_count() == 0

    def find_card(self, letter, type):
        for card in self.cards:
            if card.is_card(letter, type):
                return card
        return None

    def pull_card(self):
        random.choice(self.cards)
