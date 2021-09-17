from card import Card


CARD_LETTERS = [
    "A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1"
]

CARD_TYPES = ["heart", "clubs", "spades", "diamonds"]

CARD_VALUES = {
    11: ["A"],
    10: ["K","Q", "J", "10"]
}

for i in range(9):
    value = 9-i
    if value in CARD_VALUES:
        CARD_VALUES[value].append(str(value))
    else:
        CARD_VALUES[value] = [str(value)]

def find_card_value(letter):
    for value in CARD_VALUES:
        list_of_values = CARD_VALUES[value]
        if letter in list_of_values:
            return value
    return 0

def generate_maze():
    cards = []
    for type in CARD_TYPES:
        for letter in CARD_LETTERS:
            cards.append(Card(letter=letter, type=type, value=find_card_value(letter)))
    return cards


INITIAL_MAZE = generate_maze()

PAYLOAD_SIZE = 2048 * 2

