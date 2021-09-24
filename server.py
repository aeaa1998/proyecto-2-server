
# Python program to implement server side of chat room.
from constants import PAYLOAD_SIZE
import json
from client import Client
from room import Room
from registration import RegistrationPayload
from typing import cast
from error import ErrorResponse
import sys
from threading import Thread
import websockets
import asyncio



class Server(object):
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.starter = websockets.serve(self.start, ip_address, port)
        

        self.rooms_dictionary = {}
        self.list_of_clients = []
        self.list_of_clients_usernames = []

    async def create_or_join_room(self, connection, registration_payload, payload):
        
        username = registration_payload.username
        if payload is None:
            if registration_payload.is_new_room:
                room = Room()
                self.rooms_dictionary[room.id] = room
            else:
                room = self.rooms_dictionary[registration_payload.room_id]
            
            if room.started:
                # The game has already started so you must join to another game or create a new room
                await connection.send(room.room_filled_payload())
                return None, None

        else:
            try:
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
                    if room.started:
                        # The game has already started so you must join to another game or create a new room
                        await connection.send(room.room_filled_payload())
                        return None, None
            except:
                return None, None
        client = await self.rooms_dictionary[room.id].add_client(
            username, connection)
        await client.send_logged()
        return room.id, client

    async def registration_step(self, registration_payload, registration_payload_serialized, conn):
        try:
            if registration_payload_serialized:
                registration_payload.load(registration_payload_serialized)
                if registration_payload.username not in self.list_of_clients_usernames and not registration_payload.failed_registration:
                    self.list_of_clients_usernames.append(
                        registration_payload.username)
                    return (1, registration_payload)
                    
                elif registration_payload.failed_registration:
                    await conn.send(ErrorResponse(
                        "Ocurrio un error inesperado al registrarse por favor probar de nuevo", 400).dump())
                else:
                    await conn.send(ErrorResponse(
                        "Ese usuario ya ha sido tomado", 401).dump())
                return (0, registration_payload)
        except:
            print("Oops!", sys.exc_info()[0], "occurred.")
            return (-1, registration_payload)

    async def clientthread(self, conn, addr):
        registered_successfully = 0
        room_id = None
        client = None
        registration_payload = RegistrationPayload()
        try:
            async for message in conn:
                if registered_successfully == 0:
                    new_value, registration_payload = await self.registration_step(registration_payload, message, conn)
                    registered_successfully = new_value
                    if new_value == 1:
                        room_id, client = await self.create_or_join_room(conn, registration_payload, None)
                elif registered_successfully == -1:
                    error = ErrorResponse("Ha ocurrido un problema al establecer su conexion por favor pruebe nuevamente", 500)
                    return
                else:
                    if room_id == None or client == None:
                        room_id, client = await self.create_or_join_room(conn, registration_payload, message)
                    else:
                        # Proceed to the game
                        room = self.rooms_dictionary[room_id]
                        _continue = await self.process_payload(client, room, message)
                        if not _continue:
                            self.remove(conn, registration_payload.username)
                            return
        except websockets.exceptions.ConnectionClosed as e:
           print("a client just disconnected")
           self.remove(conn, registration_payload.username)
        except Exception:
           print("a client just disconnected")
           self.remove(conn, registration_payload.username)
           

    async def start(self, websocket, path):
        print("Client just connected")
        self.list_of_clients.append(websocket)
        await self.clientthread(websocket, None)

    def remove(self, connection, username):
        if connection in self.list_of_clients:
            self.list_of_clients.remove(connection)

        if username in self.list_of_clients_usernames:
            self.list_of_clients_usernames.remove(username)


    # Process user payload coming
    async def process_payload(self, client, room, message):
        try:
            payload = json.loads(message)
            # Player logout

            type = payload["__type__"]
            print("Message of type recieved: ", type)
            if type  == "__logout__":
                return False
            elif type  == "__room_start_update__":
                if payload["__start__"] == 1 or payload["__start__"] == True:
                    # User wants to start the game
                    await room.start_game()
                else:
                    # User dennies the game so it resets its count to 0
                    await room.reset_count(client)
            elif type == "__client_turn__":
                # In game client turn lets process it
                await room.process_turn(payload)
            elif type == "__chat__":
                # In game client turn lets process it
                await room.send_chat(payload["username"], payload["message"])
            return True
        except Exception as e:
            print("Exc ", e)
            await client.connection.send(ErrorResponse(
                        "No se pudo procesar la respuesta", 400).dump())
            return True
