import json


class ErrorResponseEncoder(json.JSONEncoder):

    def default(self, o):
        return {
            '__type__': "error",
            '__error_response_message__': o.message,
            '__error_response_code__': o.code,
        }


class ErrorResponse(object):
    def __init__(self, message, code=400) -> None:
        self.message = message
        self.code = code

    def dump(self):
        return json.dumps(self, indent=4, cls=ErrorResponseEncoder)
