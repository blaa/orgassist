
from orgassist import ConfigError
from orgassist import log, templates

"""
Assistant class and assistant plugin interfaceo
"""

class PluginError(Exception):
    "Raised when plugin causes an error"

class Assistant:
    """
    Assistant keeps a state of a single communication.
    Identifies his boss on the bots interfaces (xmpp, irc, etc.)
    Dispatches incoming messages to commands.
    """
    class Message:
        "API to unify all message data in one object"

        def __init__(self, text, sender, respond):
            self.text = text
            self.sender = sender
            self._respond = respond

        def respond(self, text):
            "Proxy to respond"
            self._respond(text)

    # {'org': OrgContext, 'calendar': CalendarNotifications,
    #  'plugin_name': PluginClass }
    registered_plugins = {}

    def __init__(self, name, config, scheduler):
        "Initialize structures, plugins and validate configs early"
        # Assistant initialization
        self.assistant_name = name
        self.scheduler = scheduler
        self.config = config

        # Instances of plugins
        self.plugins = {}

        # Global assistant state to let plugins cooperate
        self.state = {}

        # Commands registered by plugins for dispatching
        # {command1: callback1, command2: callback1,
        #  command3: callback2 }
        self.commands = {}

        self._validate_config()
        self._initialize_plugins()

    def _initialize_plugins(self):
        "Create instances of plugins"
        # {name: handler1, name2: handler1, name3: handler2, ...}
        plugins = self.config.get('plugins', assert_type=dict)

        for plugin_name, plugin_config in plugins.items():
            plugin_cls = Assistant.registered_plugins.get(plugin_name, None)
            if plugin_cls is None:
                raise ConfigError("Configured plugin '%s' is not registered" %
                                  plugin_name)

            self.state[plugin_name] = {}
            plugin = plugin_cls(self, plugin_config,
                                self.scheduler, self.state[plugin_name])
            plugin.validate_config()
            plugin.register()
            self.plugins[plugin_name] = plugin
            log.info('Plugin %s instantiated', plugin_name)

        # Initialize plugins
        for plugin in self.plugins.values():
            plugin.initialize()


    def _validate_config(self):
        "Simple config validation - fail early"
        self.config.get('plugins')
        self.config.get('boss')
        self.config.get('boss.jid')

    def register_xmpp_bot(self, bot):
        """
        Dispatch to this assistant when a JID talks to bot with given
        resource.
        """
        boss = self.config.boss
        bot.add_dispatch(boss.jid, boss.get('resource',
                                            default=None,
                                            required=False),
                         self.handle_message)

    def register_irc_bot(self, bot):
        "Register dispatch in an IRC bot"
        raise NotImplementedError

    def register_command(self, names, callback):
        "Register command dispatch"
        if isinstance(names, str):
            names = [names]
        for name in names:
            name = name.lower().strip()
            if name in self.commands:
                raise PluginError("Command '%s' was already registered." % name)
            if ' ' in name:
                raise PluginError("Commands ('%s') can't have spaces within." % name)

            self.commands[name] = callback

    def handle_message(self, text, sender, respond):
        """
        Handle command sent by the Boss.
        """

        command = text.split()[0]
        command = command.lower().strip()
        print()
        print("HH", self.commands)
        handler = self.commands.get(command, None)
        if handler is not None:
            message = self.Message(text, sender, respond)
            handler(message)
        else:
            respond(templates.get('DONT_UNDERSTAND'))

    # Decorator to register context plugins
    @classmethod
    def plugin(cls, name):
        "Decorator to register plugins within assistant"
        def decorator(plugin_cls):
            "Register and return a plugin"
            if name in cls.registered_plugins:
                raise Exception("Plugin %s already defined" % name)
            cls.registered_plugins[name] = plugin_cls
            return plugin_cls
        return decorator


class AssistantPlugin:
    """
    Handles some data state (eg. org-mode directory),
    configures scheduler and may initiate communication.
    """
    def __init__(self, assistant, config, scheduler, state):
        self.config = config
        self.scheduler = scheduler
        self.assistant = assistant
        self.state = state

    def initialize(self):
        """
        Called once at the beginning to initialize - so implementors can leave
        __init__ alone.
        """

    def validate_config(self):
        """
        Validate configuration, raise ConfigError on problems.

        Touch all valid config options here, so that Config class can report
        what config keys were ignored (and are, for example, mistyped).
        """

    def register(self):
        """
        Register commands and other callbacks.
        """
