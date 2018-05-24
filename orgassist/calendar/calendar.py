"""
org-mode compatible, agenda-focused calendar.
"""

from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin

@Assistant.plugin('calendar')
class CalendarCore(AssistantPlugin):
    pass
