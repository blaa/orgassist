from orgassist import Assistant
from orgassist.assistant import AssistantPlugin

@Assistant.plugin('org')
class OrgPlugin(AssistantPlugin):
    """
    Handle operations on an org-mode tree
    """

    def register(self, assistant):
        self.assistant = assistant
        assistant.register_command(['agenda', 'ag'],
                                   self.handle_agenda)

    def handle_agenda(self, message):
        message.respond('That is an agenda!')
        message.respond('It works!')

