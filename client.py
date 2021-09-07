class Client(object):
    def __init__(self, room_id, username, order, connection):
        self.username = username
        self.order = order
        self.room_id = room_id
        self.connection = connection
        self.lives = 4
