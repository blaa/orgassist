"""
Glue between a calendar and other plugins and bot commands.
"""

import os
import datetime as dt
import traceback as tb

from orgassist import log
from orgassist.config import ConfigError
from orgassist.assistant import Assistant, AssistantPlugin
from orgassist.calendar import Calendar

@Assistant.plugin('calendar')
class CalendarCore(AssistantPlugin):

    def initialize(self):
        # How often to check calendar and plan notifications?
        # If someone cancels an event after notification was scheduled
        # the notification will happen anyway.
        scan_interval = 120
        self.scheduler.every(scan_interval).seconds.do(self.schedule_notifications)

    def schedule_notifications(self):
        "Schedule incoming notifications"
        log.info('Would schedule notifications!')

    def validate_config(self):
        "Read config and apply defaults"
        cfg = self.config
        self.notify_before = cfg.get('notify_before_m',
                                     default=[5, 20])

        self.agenda_times = cfg.get('agenda.times',
                                    default=['7:00', '12:00'])

        #self.agenda_horizon_future = cfg.get('agenda.horizon_future',
        #                                     default=2)

        self.horizon_unfinished = cfg.get('agenda.horizon_unfinished',
                                          default=24)
        self.horizon_incoming = cfg.get('agenda.horizon_incoming',
                                        default=720)

        self.agenda_path = cfg.get_path('agenda.agenda_template_path',
                                             required=False)
        if not self.agenda_path:
            path = os.path.dirname(os.path.abspath(__file__))
            self.agenda_path = os.path.join(path,
                                            'templates',
                                            'agenda.txt.j2')

        try:
            with open(self.agenda_path):
                pass
        except IOError:
            raise ConfigError('Unable to open agenda template file: ' +
                              self.agenda_path)

    def register(self):

        self.calendar = Calendar(self.agenda_path)

        # Register calendar in global state - this is our public API
        self.state['calendar'] = self.calendar

        commands = [
            (['agenda', 'ag'], self.handle_agenda),
        ]
        for aliases, callback in commands:
            self.assistant.register_command(aliases, callback)

    def handle_agenda(self, message):
        "Respond with an agenda on agenda command"
        message.respond('That is an agenda!')
        message.respond('It works!')

        now = dt.datetime.now()
        horizon_unfinished = now - dt.timedelta(hours=self.horizon_unfinished)
        horizon_incoming = now + dt.timedelta(hours=self.horizon_incoming)

        try:
            agenda = self.calendar.get_agenda(horizon_incoming,
                                              horizon_unfinished,
                                              relative_to=now)
        except Exception:
            tb.print_exc()
            message.respond("Error while rendering Agenda template.")
            return
        message.respond(agenda)
