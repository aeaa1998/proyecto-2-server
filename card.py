
import json


class CardEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': 'card',
            '__card__': {
                'type': o.type,
                'letter': o.letter,
                'value': o.value,
            }
        }


class Card(object):
    def __init__(self, letter, type, value):
        self.type = type
        self.letter = letter
        self.value = value

    def is_card(self, letter, type):
        return self.letter == letter and self.type == type

    def toJson(self):
        return {
            '__type__': 'card',
            '__card__': {
                'type': self.type,
                'letter': self.letter,
                'value': self.value,
            }
        }

    def dump(self):
        return json.dumps(self, indent=4, cls=CardEncoder)
