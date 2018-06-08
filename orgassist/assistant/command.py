"""
Command dispatch logic extracted from assistant.
"""
from time import time

from orgassist.assistant import api
from orgassist.helpers import language

class CommandDispatch:
    """
    Dispatch incoming commands between plugins. Handles command "state".
    """

    # Number of past contexts to keep.
    KEEP_CONTEXTS = 3

    def __init__(self, assistant):
        "Create variables"

        self.assistant = assistant

        # Commands registered by plugins for dispatching
        # {command1: callback1, command2: callback1,
        #  command3: callback2 }
        self.commands = {}

        # Current command context.
        self.context = None

        # Few recent contexts.
        self.context_stack = []

    def register(self, names, callback):
        "Register command dispatch"
        # TODO: Handle regular expressions as names
        if isinstance(names, str):
            names = [names]
        for name in names:
            name = name.lower().strip()
            if name in self.commands:
                raise api.PluginError("Command '%s' was already registered." % name)
            if ' ' in name:
                raise api.PluginError("Commands ('%s') can't have spaces within." % name)

            self.commands[name] = callback

    def context_quit(self, message=None):
        """
        Quit context and inform user (if message object is passed)
        """
        ctx = self.context
        if not ctx:
            if message:
                message.respond(language.get('NO_CONTEXT'))
            return False

        self.context = None
        self.context_stack.insert(0, ctx)
        self.context_stack = self.context_stack[:self.KEEP_CONTEXTS]
        if message:
            msg = language.get("QUIT_CONTEXT").format(ctx.describe())
            message.respond(msg)
        return True

    def dispatch(self, message):
        """
        Handle command sent by the Boss.

        - Use context handler if available.
        - Otherwise match registered commands.
        - If handler returns a CommandContext - enter a new context.
        """
        command_raw = message.text.strip()
        if command_raw == '.':
            # Quit current context.
            self.context_quit(message)
            return

        # Context handler has priority
        if self.context is not None:
            ret = self.context.handler(message)
            if ret:
                self.context_quit(None)
            return

        # Generic command handling
        command_raw = command_raw.split()[0]
        command = command_raw.lower().strip()
        handler = self.commands.get(command, None)
        if handler is not None:
            # Prepare a message without a command-word.
            message.strip_command(command_raw)
            ret = handler(message)
            if isinstance(ret, api.CommandContext):
                self.context = ret
        else:
            message.respond(language.get('DONT_UNDERSTAND'))

    def enter_context(self, context):
        """
        During execution of a command, a user can enter a "command context" - and
        have further commands executed in the context of the main command.
        The single "." command always quits the context.
        """
