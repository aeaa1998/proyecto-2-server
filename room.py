from chat import Chat
from client_turn import ClientTurnDispatcher
from client import Client, ClientDiedEncoder, ClientLostLifeEncoder, ClientReviveEncoder, ClientSavedEncoder
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
                'deck': o.deck.toJson(),
                'visible_deck': o.visible_deck.toJson(),
                'started': o.started,
                "current_turn": o.current_turn,
                "start_count": o.start_count,
                # If hand_turn is present there is only one row left
                'hand_turn': o.hand_turn
            },
        }


class RoomUpdateCountEncoder(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "room_update",
            '__field__': "start_count",
            "__value__": o.start_count
        }


class RoomFinished(json.JSONEncoder):
    def default(self, o):
        return {
            '__type__': "room_finished",
            '__winner__': o.clients[0].toJson()
        }


class Room(object):
    def __init__(self):
        self.id = uuid.uuid4().hex
        self.deck = Deck()
        self.visible_deck = Deck([], False)
        self._clients = []
        self.started = False
        self.dealer = None
        self.start_count = 0
        self.current_turn = None
        self.hand_turn = None
        self.client_turn_dispatcher = ClientTurnDispatcher(room=self)
        self.chats = []

    # Only alive clients will be shown in here
    @property
    def clients(self):
        return list(filter(lambda c: c.lives > 0, self._clients))

    # Get the initial turn computed
    @property
    def initial_turn(self):
        if self.dealer is None:
            return 0
        else:
            if self.dealer.order == 1:
                return len(self.clients)
            else:
                return self.dealer.order - 1

    # Add a client to the array
    async def add_client(self, username, conn):
        client_to_add = Client(self.id, username, len(self._clients) + 1, conn)
        self._clients.append(client_to_add)
        room_dump = self.dump(RoomEncoder)
        await client_to_add.send(room_dump)
        await client_to_add.send_prescence()
        return client_to_add

    def dump(self, encoder=RoomEncoder):
        return json.dumps(self, indent=4, cls=encoder)

    async def send_chat(self, username, message):
        chat = Chat(username, message)
        chat_dump = chat.dump()
        for client in self._clients:
            if client.username != username:
                await client.send(chat_dump)

    async def dump_clients(self, encoder=RoomEncoder):
        room_dump = self.dump(encoder)
        for client in self._clients:
            await client.send(room_dump)

    async def start_game(self):
        self.start_count += 1
        clients_count = len(self._clients)
        self.started = (self.start_count ==
                        clients_count) and clients_count >= 3
        # Check if it started so notify all players
        if self.started:
            self.set_dealer()
            for client in self._clients:
                if len(client.cards) == 0:
                    initial_maze = [self.pull_card_from_deck(
                    ), self.pull_card_from_deck(), self.pull_card_from_deck()]
                    # We set the initial maze for the client
                    client.cards = initial_maze
                    await client.send_prescence()
            first_visible_card = self.pull_card_from_deck()
            self.visible_deck.add_card_top(first_visible_card)
            self.current_turn = self.initial_turn
            await self.dump_clients()
        else:
            # We must update the counter to everyone
            room_dump = self.dump(encoder=RoomUpdateCountEncoder)
            for client in self._clients:
                await client.connection.send(room_dump)

    async def reset_count(self, client):
        # Notify all players they must ask again to start
        self.start_count = 0
        room_dump = self.dump()
        for c in self._clients:
            # The player that said no already knows that the game does not need to be restarted
            if c.username != client.usermane:
                await c.connection.send(room_dump)

    # Set new client order

    def set_client_order(self):
        for index, client in enumerate(self.clients):
            client.order = index + 1

    async def reset_row(self):
        self.visible_deck.reset_cards()
        self.deck.reset_cards()
        self.current_turn = self.initial_turn
        if self.current_turn == 1:
            self.current_turn = len(self.clients)
        else:
            self.current_turn -= 1
        self.hand_turn = None
        print("cleaned")
        for client in self.clients:
            client.reset(False)
            initial_maze = [self.pull_card_from_deck(
            ), self.pull_card_from_deck(), self.pull_card_from_deck()]
            # We set the initial maze for the client
            client.cards = initial_maze
        self.set_client_order()
        self.set_dealer()
        first_visible_card = self.pull_card_from_deck()
        self.visible_deck.add_card_top(first_visible_card)
        for client in self.clients:
            print("sending prescence")
            await client.send_prescence()

        await self.dump_clients()
        print("sending room")

    # Restart the room to its original form
    async def reset_room(self):
        self.visible_deck.reset_cards()
        self.deck.reset_cards()
        self.start_count = 0
        self.started = False
        room_dump = self.dump()
        self.current_turn = None
        self.hand_turn = None
        print("vars reset")
        for client in self._clients:
            client.reset()
        self.set_client_order()
        for client in self.clients:
            await client.connection.send(room_dump)
            await client.send_prescence()

    def remove_client(self, username):
        for client in self._clients:
            if client.username == username:
                self._clients.remove(client)
                return

    async def process_hand(self):
        if self.hand_turn is None:
            self.hand_turn = self.current_turn
            self.next_turn()
            await self.dump_clients()
        else:
            next_turn = (self.current_turn % len(self.clients)) + 1
            # If next turn we finish
            if next_turn == self.hand_turn:
                # We finish the round
                lowest_value = 40
                there_is_draw = False
                for client in self.clients:
                    if lowest_value > client.hand.value:
                        lowest_value = client.hand.value
                        there_is_draw = False
                    elif lowest_value == client.hand.value:
                        there_is_draw = True
                died_clients = []
                # There was a draw no one looses
                if there_is_draw:
                    for client in self.clients:
                        await client.send_life_prescence(ClientSavedEncoder)
                    await self.reset_row()
                # Notify all losers
                else:
                    for client in self.clients:
                        if client.hand.value == lowest_value:
                            if client.order == self.hand_turn:
                                client.lives -= 2
                            else:
                                client.lives -= 1

                            if client.lives <= 0:
                                died_clients.append(client)
                            await client.send_life_prescence(ClientLostLifeEncoder)

                        else:
                            await client.send_life_prescence(ClientSavedEncoder)

                    # Everyone is dead so all the ones that died will be revived with 1 live
                    if len(self.clients) == 0:
                        for dead_client in died_clients:
                            await dead_client.send_life_prescence(ClientReviveEncoder)
                            dead_client.lives = 1
                    # Game finished
                    elif len(self.clients) == 1:
                        await self.dump_clients(RoomFinished)
                        await self.reset_room()
                    # We proceed to the next round with the remaining
                    else:
                        # Notify the dead clients
                        # for dead_client in died_clients:
                        #     await client.send_life_prescence(ClientDiedEncoder)
                        await self.reset_row()
            else:
                self.next_turn()
                await self.dump_clients()

    def next_turn(self):
        self.current_turn = (self.current_turn % len(self.clients)) + 1

    def set_dealer(self):
        self.dealer = random.choice(self.clients)
        self.dealer.is_dealer = True

    async def process_turn(self, turn_json):
        await self.client_turn_dispatcher.process(turn_json)

    def pull_card_from_deck(self, deck="deck"):
        if deck == "deck":
            return self.deck.pull_card()
        return self.visible_deck.pull_card(0)

    def room_filled_payload(self):
        return json.dumps({'__type__': 'room_filled'}, indent=4)

    def find_client(self, username):
        for client in self._clients:
            if client.username == username:
                return client
        return None
