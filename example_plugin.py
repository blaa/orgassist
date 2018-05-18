"""
An example of a simple plugin which showcases all the basic API.
"""

from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin

@Assistant.plugin('owa')
class OwaPlugin(AssistantPlugin):
    """
    An example of a simple orgassist plugin.
    """

    def validate_config(self):
        """
        Called first: Use this method to read config parameters and substitute
        defaults were appropriate.

        You should touch all your config variables here so we can inform the
        user if he have mistyped something in the config file (even when --test
        parameter is given)

        Available API: self.config, self.assistant, self.scheduler.
        self.state might not be fully populated and ready yet.
        """
        log.info("1. Validate and read config")
        self.parameter = self.config.get('parameter',
                                         assert_type=int,
                                         default=42)
    def register(self):
        """
        Called second: Use this method to register any commands/callbacks via the
        self.assistant API.
        """
        log.info("2. Register plugin commands")

        # You can register some commands here
        commands = [
            (['owa_refresh'], self.handle_refresh),
        ]
        for aliases, callback in commands:
            self.assistant.command.register(aliases, callback)

    def initialize(self):
        """
        Called third, after all plugins are registered. Use it to initialize the
        plugin.

        It's a good place to register periodic callbacks using self.scheduler.
        You can also use other plugins public API via the self.state object.
        """
        log.info("3. Initialize the plugin")

        # There might be some operation you need to do periodically:
        self.scheduler.every(30).seconds.do(self.periodic)

    def handle_refresh(self, message):
        "Example: Command executed"
        reply = "You (%s) have sent: %s (parameter: %d)" % (message.sender, message.text,
                                                            self.parameter)
        message.respond(reply)

    def periodic(self):
        "Example: Periodic operations"
        log.info("Periodic operation executed")

        # Use shared state to talk to core plugins
        self.state['calendar'].add_events([], 'owa')
