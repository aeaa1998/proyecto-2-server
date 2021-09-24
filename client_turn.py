from card import Card
from constants import find_card_value
import json


class EndedTurn(object):
    def __init__(self):
        self.lol = ""

    async def process(self, room):
        # # Next turn is allowed
        room.next_turn()
        # Notify users that the room decks have changed
        await room.dump_clients()
        print("Notified users for next turn")

class DiscardedCard(object):
    def __init__(self, turn_json):
        self.card = Card(letter=turn_json["letter"], type=turn_json["card_type"], value=find_card_value(turn_json["letter"]))
        self.client_username = turn_json["username"]

    async def process(self, room):
        client = room.find_client(self.client_username)
        client.discard_card(self.card)
        # Update the new decks
        room.visible_deck.add_card_top(self.card)
        # # Next turn is allowed
        # room.next_turn()
        # Notify users that the room decks have changed
        await room.dump_clients()
        print("Notified users for decks")

class AskForCard(object):
    def __init__(self, turn_json):
        self.client_username = turn_json["username"]
        self.deck = turn_json["deck_origin"]

    async def process(self, room):
        client = room.find_client(self.client_username)
        new_card = room.pull_card_from_deck(self.deck)
        # Update the new information of the client
        await client.add_card(new_card)
        # await client.send_prescence()
        # Update the new decks
        await room.dump_clients()
        # await client.send_can_pull_card()


class ClientHand(object):
    def __init__(self, turn_json):
        c_j = turn_json["cards"]
        # Incase the json is sent as an string
        if isinstance(c_j, str):
            c_j = json.loads(c_j)
        

        self.cards =  [Card(letter=card["letter"], type=card["type"], value=find_card_value(card["letter"])) for card in c_j]
        self.client_username = turn_json["username"]
        self.value = self.get_hand_value()
    
    def get_hand_value(self):
        if len(self.cards) > 1:
            letter = self.cards[0].letter
            if len(self.cards) == 3 and all(card.letter == letter for card in self.cards):
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

    async def process(self, room):
        client = room.find_client(self.client_username)
        client.hand = self
        print(client.username)
        print(client.hand.value)
        await room.process_hand()


class ClientTurnDispatcher(object):
    def __init__(self, room):
        self.room = room

    def deserialize(self, turn_json):
        if turn_json["type"] == "discard_card":
            return DiscardedCard(turn_json)
        elif turn_json["type"] == "pull_card":
            return AskForCard(turn_json)
        elif turn_json["type"] == "present_hand":
            print("PRESENTING CARD")
            return ClientHand(turn_json)
        elif turn_json["type"] == "end_turn":
            return EndedTurn()
        return None
        
    async def process(self, turn_json):
        response = self.deserialize(turn_json)
        if response is not None:
            await response.process(self.room)
        
