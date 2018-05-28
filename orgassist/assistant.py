
from orgassist.config import ConfigError
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

        # List of callbacks to call boss when initiating communication
        self.boss_channels = []

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

            plugin = plugin_cls(self, plugin_config,
                                self.scheduler, self.state)
            plugin.validate_config()
            plugin.register()
            self.plugins[plugin_name] = plugin
            log.info('Plugin %s instantiated', plugin_name)

        # After all plugins are created - initialize plugins
        for plugin in self.plugins.values():
            plugin.initialize()


    def _validate_config(self):
        "Simple config validation - fail early"
        self.config.get('plugins')
        self.config.get('channels')

    def register_xmpp_bot(self, bot):
        """
        Dispatch to this assistant when a JID talks to bot with given
        resource.
        """
        for channel_cfg in self.config.channels:
            jid = channel_cfg.get('jid',
                                  required=False, assert_type=str)
            resource = channel_cfg.get('resource',
                                       required=False, assert_type=str)
            # FUTURE: Calling by name.
            # name = channel_cfg.get('name', default='boss')

            if not jid:
                continue

            # Incoming channel
            bot.add_dispatch(jid, resource,
                             self.handle_message)

            # Outgoing channel
            def create_closure(jid, resource):
                "Create closure containing JID and resource"
                def out(msg):
                    "Outgoing channel to the boss"
                    send_to = jid
                    if resource is not None:
                        send_to += '/' + resource
                    print("OUT TO", send_to)
                    bot.send_message(send_to, msg)
                self.boss_channels.append(out)

            create_closure(jid, resource)

    def register_irc_bot(self, bot):
        "Register dispatch in an IRC bot"
        raise NotImplementedError

    def register_command(self, names, callback):
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

    def handle_message(self, message):
        """
        Handle command sent by the Boss.
        """
        command = message.text.split()[0]
        command = command.lower().strip()
        handler = self.commands.get(command, None)
        if handler is not None:
            handler(message)
        else:
            message.respond(templates.get('DONT_UNDERSTAND'))

    def tell_boss(self, message):
        """
        Send message to boss using all registered channels.

        TODO: Allow to specifying priority or best channel.
        """
        for channel in self.boss_channels:
            channel(message)

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

    for_all[validate_config -> register] -> for_all[initialize]
    """

    def __init__(self, assistant, config, scheduler, state):
        """
        Args:
          assistant: Connected assistant object
          config: Part of config which is relevant to the plugin
          scheduler: Common scheduler which gets executed in the main loop
          state: a state shared between the plugins.
        """
        self.config = config
        self.scheduler = scheduler
        self.assistant = assistant
        self.state = state

    def register(self):
        """
        Register commands and other callbacks.

        Called first, before all plugins are created.
        """
        raise NotImplementedError

    def initialize(self):
        """
        Called once at the beginning to initialize - so implementors can leave
        __init__ alone. All plugins are registered when this method is called.
        """
        raise NotImplementedError

    def validate_config(self):
        """
        Validate configuration, raise ConfigError on problems.

        Touch all valid config options here, so that Config class can report
        what config keys were ignored (and are, for example, mistyped).
        """

