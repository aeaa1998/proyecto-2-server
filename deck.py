from card import Card
from constants import generate_maze
import random
import json


class DeckDecoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': 'deck',
            '__deck__': {
                'is_visible': o.is_visible,
                'cards': json.dumps([card.toJson() for card in o.cards]),
                'card_count': o.card_count
            }
        }


class Deck(object):
    def __init__(self, cards=generate_maze(), is_visible=False):
        copy = cards.copy()
        random.shuffle(copy)
        self.cards = copy
        self._initial_cards = copy.copy()
        self.is_visible = is_visible

    def reset_cards(self):
        copy = self._initial_cards.copy()
        random.shuffle(copy)
        self.cards = copy

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

    def add_card_top(self, card):
        return self.cards.insert(0, card)
        

    def pull_card(self, index=None):
        _index = index
        if _index is None:
            _index = random.randrange(len(self.cards))
        return self.cards.pop(_index)


    def toJson(self):
        return{
            '__type__': 'deck',
            '__deck__': {
                'is_visible': self.is_visible,
                'cards': json.dumps([card.toJson() for card in self.cards]),
                'card_count': self.card_count
            }
        }
    def dump(self):
        return json.dumps(self, indent=4, cls=DeckDecoder)