
# Main logger
import logging
log = logging.getLogger('orgassist')

from . import config
from . import calendar
from . import bots

from .assistant import PluginError
from .assistant import Assistant, AssistantPlugin


# Register commands
from . import plugins
