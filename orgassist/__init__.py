
# Main logger
import logging
log = logging.getLogger('orgassist')

from .config import Config, ConfigError
from .bots import XmppBot
from .assistant import Assistant

from . import orgnode

# Register commands
from . import plugins
