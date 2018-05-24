
# Main logger
import logging
log = logging.getLogger('orgassist')

from . import config
from . import calendar
from . import bots
from . import assistant

# Register commands
from . import plugins
