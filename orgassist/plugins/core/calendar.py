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
        # Initialize schedulers
        scan_interval = 120
        self.scheduler.every(scan_interval).seconds.do(self.schedule_notifications)
        for time in self.agenda_times:
            self.scheduler.every().day.at(time).do(self.send_agenda)

        # Incoming notifications
        self.notify_dedups = []
        for time in self.agenda_times:
            delta = dt.timedelta(minutes=time)

    def schedule_notifications(self):
        "Schedule incoming notifications"

        # Program may hang for indefinite amount of time and we still should
        # not miss any notifications. At the same time calendar may get updated,
        # tasks added or removed. We can't send duplicates.

        # Prepare notification 5 minutes before it happens
        prepare_before = 5

        now = dt.datetime.now()

        # Build an incoming list of stuff that WILL get notifications

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
            print("No path in config file")
            path = os.path.dirname(os.path.abspath(__file__))
            self.agenda_path = os.path.join(path,
                                            'templates',
                                            'agenda.txt.j2')

        try:
            print("Trying agenda:", self.agenda_path)
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
        agenda = self.get_agenda()
        print("Returning agenda:", agenda)
        message.respond(agenda)

    def get_agenda(self):
        "Generate agenda"
        now = dt.datetime.now()
        horizon_unfinished = now - dt.timedelta(hours=self.horizon_unfinished)
        horizon_incoming = now + dt.timedelta(hours=self.horizon_incoming)

        try:
            agenda = self.calendar.get_agenda(horizon_incoming,
                                              horizon_unfinished,
                                              relative_to=now)
            return agenda
        except Exception:
            tb.print_exc()
            return "Error while rendering Agenda template."

    def send_agenda(self):
        "Used for sending periodically agenda"
        agenda = self.get_agenda()
        self.assistant.tell_boss(agenda)
