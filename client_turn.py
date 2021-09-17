from room import Room
from card import Card
from constants import find_card_value

class DiscardedCard(object):
    def __init__(self, turn_json):
        self.card = Card(letter=turn_json["letter"], type=turn_json["type"], value=find_card_value(turn_json["letter"]))
        self.client_username = turn_json["username"]
        self.deck = turn_json["deck_origin"]

    def process(self, room):
        client = room.find_client(self.client_username)
        client.discard_card(self.card)
        # Update the new decks
        room.visible_deck.add_card_top(self.card)
        # Notify users that the room decks have changed
        room.dump_clients()
        # Next turn is allowed
        room.next_turn()

class AskForCard(object):
    def __init__(self, turn_json):
        self.client_username = turn_json["username"]
        self.deck = turn_json["deck_origin"]

    def process(self, room):
        client = room.find_client(self.client_username)
        new_card = room.pull_card_from_deck(self.deck)
        client.add_card(new_card)
        # Update the new information of the client
        client.send_prescence()
        # Update the new decks
        room.dump_clients()
        client.send_can_pull_card()


class ClientHand(object):
    def __init__(self, turn_json):
        self.cards =  [Card(letter=card["letter"], type=card["type"], value=find_card_value(card["letter"])) for card in turn_json["cards"]]
        self.client_username = turn_json["username"]
        self.value = self.get_hand_value()
    
    def get_hand_value(self):
        if len(self.cards) > 1:
            type = self.cards[0].type
            if len(self.cards) == 3 and all(card.type == type for card in self.cards):
                # Three of same type is worth 30 points
                return 30
            # Else we compute the value
            value = 0
            for card in self.cards:
                value += card.value
            return value
        elif len(self.cards) == 0:
            return 0
        else:
            return self.cards[0].value

    def process(self, room):
        client = room.find_client(self.client_username)
        client.hand = self
        room.process_hand()


class ClientTurnDispatcher(object):
    def __init__(self, room):
        self.room = room

    def deserialize(self, turn_json):
        if turn_json["type"] == "discard_card":
            return DiscardedCard(turn_json)
        if turn_json["type"] == "pull_card":
            return AskForCard(turn_json)
        if turn_json["type"] == "present_hand":
            return DiscardedCard(turn_json)
        return None
        
    def process(self, turn_json):
        response = self.deserialize(turn_json)
        if response is not None:
            response.process(self.room)
        
