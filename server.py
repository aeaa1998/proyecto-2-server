
# Python program to implement server side of chat room.
from constants import PAYLOAD_SIZE
import json
from client import Client
from room import Room
from registration import RegistrationPayload
from typing import cast
from error import ErrorResponse
import socket
import select
import sys
from _thread import *
from threading import Thread


class Server(object):
    def __init__(self, ip_address, port):
        """The first argument AF_INET is the address domain of the
        socket. This is used when we have an Internet Domain with
        any two hosts The second argument is the type of socket.
        SOCK_STREAM means that data or characters are read in
        a continuous flow."""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ip_address = ip_address
        self.port = port
        self.server.bind((ip_address, port))
        """
        listens for 100 active connections. This number can be
        increased as per convenience.
        """
        self.server.listen(100)
        self.rooms_dictionary = {}
        self.list_of_clients = []
        self.list_of_clients_usernames = []

    def create_or_join_room(self, connection, registration_payload):
        username = registration_payload.username
        if registration_payload.is_new_room:
            room = Room()
            self.rooms_dictionary[room.id] = room
        else:
            room = self.rooms_dictionary[registration_payload.room_id]
        while room.started:
            # The game has already started so you must join to another game or create a new room
            connection.send(room.room_filled_payload())
            try:
                payload = connection.recv(PAYLOAD_SIZE)
                if payload:
                    json_payload = json.load(payload)
                    if json_payload['__type__'] == "new_room":
                        room = Room()
                        self.rooms_dictionary[room.id] = room
                    elif json_payload['__type__'] == "join_room":
                        room = self.rooms_dictionary[json_payload['room_id']]
                    elif json_payload['__type__'] == "logout":
                        self.remove(connection, registration_payload.username)
                        return None, None
                else:
                    self.remove(connection, registration_payload.username)
                    return None, None

            except:
                print("")
        client = self.rooms_dictionary[room.id].add_client(
            username, connection)
        return room.id, client


    def clientthread(self, conn, addr):
        registered_successfully = 0
        registration_payload = RegistrationPayload()
        while registered_successfully == 0:
            try:
                registration_payload_serialized = conn.recv(PAYLOAD_SIZE)
                registration_payload.load(registration_payload_serialized)
                if registration_payload.username not in self.list_of_clients_usernames and not registration_payload.failed_registration:
                    registered_successfully = 1
                    self.list_of_clients_usernames.append(
                        registration_payload.username)
                elif registration_payload.failed_registration:
                    conn.send(ErrorResponse(
                        "Ocurrio un error inesperado al registrarse por favor probar de nuevo", 400).dump())
                else:
                    conn.send(ErrorResponse(
                        "Ese usuario ya ha sido tomado", 401).dump())
            except:
                registered_successfully == -1

        if registered_successfully == -1:
            error = ErrorResponse(
                "Ha ocurrido un problema al establecer su conexion por favor pruebe nuevamente", 500)
            conn.send(error.dump())
            self.remove(conn, registration_payload.username)
            return

        registered_successfully = None
        room_id, client = self.create_or_join_room(conn, registration_payload)
        # We did not connect to a room we must logout
        if room_id == None or client == None:
            return
        
        room = self.rooms_dictionary[room_id]
        # Lets process the responses
        while True:
            try:
                payload = conn.recv(PAYLOAD_SIZE)
                if payload:
                    self.process_payload(client, room, payload)
                else:
                    # We are removed from the room also
                    room.remove_client(client.username)
                    self.remove(conn, registration_payload.username)

            except:
                print("")


    def start(self):
        while True:

            """Accepts a connection request and stores two parameters,
            conn which is a socket object for that user, and addr
            which contains the IP address of the client that just
            connected"""
            conn, addr = self.server.accept()

            """Maintains a list of clients for ease of broadcasting
            a message to all available people in the chatroom"""
            self.list_of_clients.append(conn)

            # prints the address of the user that just connected
            print(addr[0] + " connected")

            # creates and individual thread for every user
            # that connects
            # Thread(target=self)
            start_new_thread(self.clientthread, (self, conn, addr))
        conn.close()
        server.close()

    """The following function simply removes the object
    from the list that was created at the beginning of
    the program"""

    def remove(self, connection, username):
        if connection in self.list_of_clients:
            self.list_of_clients.remove(connection)

        if username in self.list_of_clients_usernames:
            self.list_of_clients_usernames.remove(username)

    
    # Process user payload coming
    def process_payload(self, client, room, message):
        try:
            payload = json.loads(message)
            # Player logout
            type = payload["__type__"]
            if type  == "__logout__":
                return False
            elif type  == "__room_start_update__":
                if payload["__start__"] == 1 or payload["__start__"] == True:
                    # User wants to start the game
                    room.start_game()
                else:
                    # User dennies the game so it resets its count to 0
                    room.reset_count(client)
            elif type == "__client_turn__":
                # In game client turn lets process it
                room.process_turn(payload["turn"])
            return True
        except:
            client.connection.send(ErrorResponse(
                        "No se pudo procesar la respuesta", 400).dump())
            return True
