
# Python program to implement server side of chat room.
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

        client = self.rooms_dictionary[room.id].add_client(
            username, connection)
        return room.id, client

    def clientthread(self, conn, addr):
        registered_successfully = 0
        registration_payload = RegistrationPayload()
        while registered_successfully == 0:
            try:
                registration_payload_serialized = conn.recv(2048)
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
        while True:
            try:
                message = conn.recv(2048)
                if message:

                    """prints the message and address of the
                    user who just sent the message on the server
                    terminal"""
                    print("<" + addr[0] + "> " + message)

                    # Calls broadcast function to send message to all
                    message_to_send = "<" + addr[0] + "> " + message
                    self.broadcast(message_to_send, conn)

                else:
                    """message may have no content if the connection
                    is broken, in this case we remove the connection"""
                    self.remove(conn, registration_payload.username)

            except:
                print("")
                # continue

    """Using the below function, we broadcast the message to all
    clients who's object is not the same as the one sending
    the message """

    def broadcast(self, message, connection):
        for clients in self.list_of_clients:
            if clients != connection:
                try:
                    clients.send(message)
                except:
                    clients.close()

                    # if the link is broken, we remove the client
                    self.remove(clients)

    """The following function simply removes the object
    from the list that was created at the beginning of
    the program"""

    def remove(self, connection, username):
        if connection in self.list_of_clients:
            self.list_of_clients.remove(connection)

        if username in self.list_of_clients_usernames:
            self.list_of_clients_usernames.remove(username)

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
            Thread(target=self)
            start_new_thread(self.clientthread, (self, conn, addr))

        conn.close()
        server.close()
