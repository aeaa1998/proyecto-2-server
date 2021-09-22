
from server import Server
import asyncio

# Create a server
server = Server(ip_address='localhost', port=4223)
# Start tge server
asyncio.get_event_loop().run_until_complete(server.starter)
asyncio.get_event_loop().run_forever()