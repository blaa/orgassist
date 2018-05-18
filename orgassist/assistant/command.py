"""
Command dispatch logic extracted from assistant.
"""

from orgassist.assistant import PluginError
from orgassist.helpers import language

class CommandDispatch:
    """
    Dispatch incoming commands between plugins. Handles command "state".
    """

    def __init__(self, assistant):
        "Create variables"

        self.assistant = assistant
        
        # Commands registered by plugins for dispatching
        # {command1: callback1, command2: callback1,
        #  command3: callback2 }
        self.commands = {}

    def register(self, names, callback):
        "Register command dispatch"
        # TODO: Handle regular expressions as names
        if isinstance(names, str):
            names = [names]
        for name in names:
            name = name.lower().strip()
            if name in self.commands:
                raise PluginError("Command '%s' was already registered." % name)
            if ' ' in name:
                raise PluginError("Commands ('%s') can't have spaces within." % name)

            self.commands[name] = callback

    def dispatch(self, message):
        """
        Handle command sent by the Boss.
        """
        command_raw = message.text.split()[0]
        command = command_raw.lower().strip()
        handler = self.commands.get(command, None)
        if handler is not None:
            # Prepare a message without a command.
            message.strip_command(command_raw)
            handler(message)
        else:
            message.respond(language.get('DONT_UNDERSTAND'))

