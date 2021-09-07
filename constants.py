from card import Card


CARD_LETTERS = [
    "A", "K", "Q", "J", "10", "9", "8", "7", "6", "6", " 4", "3", "2", "1"
]

CARD_TYPES = ["heart", "clubs", "spades", "diamonds"]


def generate_maze():
    cards = []
    for type in CARD_TYPES:
        for letter in CARD_LETTERS:
            cards.append(Card(letter=letter, type=type))
    return cards


INITIAL_MAZE = generate_maze()
