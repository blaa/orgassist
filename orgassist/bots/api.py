
class Message:
    "API to unify all message data in one object"

    def __init__(self, text, sender, respond):
        self.text = text
        self.sender = sender
        self._respond = respond

    def respond(self, text):
        "Proxy to respond"
        self._respond(text)

