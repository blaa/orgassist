class Message:
    "API to unify all message data in one object"

    def __init__(self, text, sender, respond):
        self.text = text
        self.sender = sender
        self.orig_text = text
        self._respond = respond

    def respond(self, text):
        "Proxy to respond"
        self._respond(text)

    def finish(self):
        """
        Call when current block of calls to respond() is done

        This does nothing for XMPP, but might be used to group multiple
        messages for other bot interfaces.
        """

    def strip_command(self, command):
        "Strip command-word from the message"
        new_text = self.text.replace(command, '', 1).lstrip()
        self.orig_text = self.text
        self.text = new_text
