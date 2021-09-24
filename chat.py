import json

class Chat(object):
    def __init__(self, username, message):
        self.username = username
        self.message = message

    def dump(self):
        return json.dumps({
            "__type__": "chat",
            "__chat__": {
                "username": self.username,
                "message": self.message,
            }
        })