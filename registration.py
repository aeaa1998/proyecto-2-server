import json


class RegistrationPayload(object):
    def __init__(self):
        self.username = None
        self.room_id = None
        self.failed_registration = False

    @property
    def is_new_room(self):
        return self.room_id == None

    def load(self, json_serialization):
        self.failed_registration = False
        try:
            json_o = json.loads(json_serialization)
            self.__dict__.update(json_o["__registration__"])
            print(json_o)
        except:
            self.failed_registration = True


        