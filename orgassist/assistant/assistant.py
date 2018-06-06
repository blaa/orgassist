"""
Assistant class and assistant plugin interfaceo
"""

from orgassist import log
from orgassist.config import ConfigError
from orgassist import helpers

from orgassist.assistant import CommandDispatch

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

        # Command dispatcher.
        self.command = CommandDispatch(self)

        # Time-related helpers
        timezone = self.config.get('timezone',
                                  default='UTC', assert_type=str)
        self.time = helpers.Time(timezone)

        # Instances of plugins
        self.plugins = {}

        # Global assistant state to let plugins cooperate
        self.state = {}

        # List of callbacks to call boss when initiating communication
        self.boss_channels = []

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
                                self.scheduler,
                                self.time, self.state)
            plugin.validate_config()
            plugin.register()
            self.plugins[plugin_name] = plugin
            log.info('Plugin %s instantiated', plugin_name)

        # After all plugins are created - initialize plugins
        for plugin in self.plugins.values():
            plugin.initialize()

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
                             self.command.dispatch)

            # Outgoing channel
            def create_closure(jid, resource):
                "Create closure containing JID and resource"
                def out(msg):
                    "Outgoing channel to the boss"
                    send_to = jid
                    if resource is not None:
                        send_to += '/' + resource
                    log.debug("Message to %s, body: %s", send_to, msg)
                    bot.send_message(send_to, msg)
                self.boss_channels.append(out)

            create_closure(jid, resource)

    def register_irc_bot(self, bot):
        "Register dispatch in an IRC bot"
        raise NotImplementedError

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
