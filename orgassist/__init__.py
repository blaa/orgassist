
# Main logger
import logging
log = logging.getLogger('orgassist')

from .config import Config, ConfigError
from .xmpp_bot import XmppBot
from .assistant import Assistant

# Register commands
from . import plugins
