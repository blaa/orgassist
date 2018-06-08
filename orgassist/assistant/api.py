"""
Assistant API plugin
"""
from time import time

class PluginError(Exception):
    """
    Raised when plugin causes a basic programming error
    """

class AssistantPlugin:
    """
    Handles some data state (eg. org-mode directory),
    configures scheduler and may initiate communication.

    for_all[validate_config -> register] -> for_all[initialize]
    """

    def __init__(self, assistant, config, scheduler, time, state):
        """
        Args:
          assistant: Connected assistant object
          config: Part of config which is relevant to the plugin
          scheduler: Common scheduler which gets executed in the main loop
          state: a state shared between the plugins.
          time: time helpers
        """
        self.config = config
        self.scheduler = scheduler
        self.assistant = assistant
        self.time = time
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


class CommandContext:
    """
    When command handler returns instance of this class it gets registered as
    current context and handles messeges instead until user closes context
    (with single ".") or context timeouts.
    """

    def __init__(self, ttl=60*10):
        "Set basic configuration"
        self._ttl = ttl
        self.refresh()

    def refresh(self):
        "Refresh/set creation time"
        self._stamp = time()

    def is_valid(self):
        "Is this context still valid?"
        now = time()
        return self._stamp + self._ttl > now

    def handler(self, message):
        """
        Handles all messages while in context

        Return True to quit context.
        """
        raise NotImplementedError

    def describe(self):
        "Describe context for user"
        return "unknown with ttl=%d" % self._ttl
