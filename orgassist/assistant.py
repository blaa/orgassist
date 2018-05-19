import functools
from . import templates

class Assistant:
    """
    """
    # [([command1, command2], Handler), ...)
    handler_classes = []

    def __init__(self, name, cfg, scheduler):
        self.scheduler = scheduler
        self.name = name
        self.cfg = cfg
        self.initialize_handlers()
        self._validate_config()

    @classmethod
    def register_handler(cls, names, handler):
        "Register assistant command"
        cls.handler_classes.append((names, handler))

    def initialize_handlers(self):
        "Create instances of command handlers"
        # {name: handler1, name2: handler1, name3: handler2, ...}
        self.handlers = {}
        for names, Handler in Assistant.handler_classes:
            handler = Handler(self, self.scheduler)
            for name in names:
                self.handlers[name] = handler

    def _validate_config(self):
        "Simple config validation - fail early"
        assert 'org' in self.cfg
        assert 'opts' in self.cfg

        assert 'boss' in self.cfg
        assert 'jid' in self.cfg['boss']

    def register_xmpp_bot(self, bot):
        boss = self.cfg['boss']
        bot.add_dispatch(boss['jid'], boss.get('resource', None),
                         self.handle_message)

    def register_irc_bot(self, bot):
        raise NotImplementedError

    def handle_message(self, respond, sender, message):
        """
        Handle command sent by the Boss.
        """
        print("GOT MESSAGE!", respond, sender, message)

        command = message.split()[0]
        command = command.lower().strip()
        print()
        print("HH", self.handlers)
        handler = self.handlers.get(command, None)
        if handler is not None:
            handler.message(respond, sender, message)
        else:
            respond(templates.get('DONT_UNDERSTAND'))


class CommandHandler:
    """
    Command handler interface
    """
    def __init__(self, assistant, scheduler):
        self.assistant = assistant
        self.scheduler = scheduler

    def message(self, respond, sender, message):
        raise NotImplementedError

# Decorator to register command handler
def command(names):
    # Register
    def decorator(handler_cls):
        Assistant.register_handler(names, handler_cls)
        return handler_cls
    return decorator
