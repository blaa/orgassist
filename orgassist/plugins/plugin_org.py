from orgassist import Assistant
from orgassist.assistant import AssistantPlugin

from orgassist.orgnode import orghelpers

@Assistant.plugin('org')
class OrgPlugin(AssistantPlugin):
    """
    Handle operations on an org-mode tree
    """

    def refresh_db(self):
        "Refresh/load DB with org entries"


    def register(self):
        commands = [
            (['agenda', 'ag'], self.handle_agenda),
        ]
        for aliases, callback in commands:
            self.assistant.register_command(aliases, callback)

    def handle_agenda(self, message):
        "Respond with an agenda on agenda command"
        message.respond('That is an agenda!')
        message.respond('It works!')
