
import json


class CardEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': 'card',
            'card': {
                'type': o.type,
                'letter': o.letter,
            }
        }


class Card(object):
    def __init__(self, letter, type, value):
        self.type = type
        self.letter = letter
        self.value = value

    def is_card(self, letter, type):
        return self.letter == letter and self.type == type

    def dump(self):
        return json.dumps(self, indent=4, cls=CardEncoder)
