from .assistant import command
from .assistant import CommandHandler


@command(["agenda"])
class AgendaHandler(CommandHandler):

    def message(self, respond, sender, message):
        respond("Yes... that is an agenda")
        respond("Does it work?")
        return "Well. That was unexpected"
