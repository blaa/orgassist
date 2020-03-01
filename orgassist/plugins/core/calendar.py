"""
Glue between a calendar and other plugins and bot commands.
"""

import datetime as dt
import traceback as tb
import schedule

from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin
from orgassist.calendar import Calendar
from orgassist import helpers

from .search import SearchContext

@Assistant.plugin('calendar')
class CalendarCore(AssistantPlugin):

    def initialize(self):
        # Scan calendar periodically and schedule notifications
        self.scheduler.every(self.scan_interval).seconds.do(self.schedule_notifications)

        # At certain points of day remind boss about agenda.
        for time in self.agenda_times:
            try:
                self.scheduler.every().day.at(time).do(self.send_agenda)
            except schedule.ScheduleValueError:
                log.error("Invalid agenda time specified '%s', use HH:MM format",
                          time)
                raise

        # When scheduling notifications, store time of last scheduled event so
        # it won't be scheduled again. Do it separately for each
        self.notify_positions = {
            delta: self.time.now() + dt.timedelta(minutes=delta)
            for delta in self.notify_periods
        }

    def send_notice(self, event):
        "Notify user in advance about incoming event."
        # Read just-in-time so it can be updated without restarting.
        template = helpers.get_template(self.notice_path)
        notice = event.format_notice(template, self.time.now())

        self.assistant.tell_boss(notice)

        # Do it always once only.
        return schedule.CancelJob

    def schedule_notifications(self):
        "Schedule incoming notifications"

        # Program may hang for indefinite amount of time and we still should
        # not miss any notifications. At the same time calendar may get updated,
        # tasks added or removed. We can't send duplicates.

        # Prepare incoming notifications up to 5 minutes before
        window_size = 5

        now = self.time.now()

        for notify_period in self.notify_periods:
            # Calculate window
            wnd_start = now + dt.timedelta(minutes=notify_period)
            wnd_end = wnd_start + dt.timedelta(minutes=window_size)
            wnd_start = max(wnd_start, self.notify_positions[notify_period])

            last_scheduled = wnd_start
            for event in self.calendar.events:
                # Ignore date-less events
                if event.relevant_date is None:
                    continue

                date = event.relevant_date.sort_date
                # We want to schedule an event if it lies between now+notify_period and
                # now+notify_period+prepare_before

                if not event.relevant_date.appointment:
                    continue

                if date <= wnd_start:
                    continue
                if date > wnd_end:
                    continue

                log.info("Scheduling %dm notification for event %r", notify_period, event)
                delta = (date - self.time.now()).total_seconds() - notify_period * 60
                self.scheduler.every(delta).seconds.do(self.send_notice, event)
                last_scheduled = max(last_scheduled, date)

            self.notify_positions[notify_period] = last_scheduled


    def validate_config(self):
        "Read config and apply defaults"
        cfg = self.config
        self.notify_periods = cfg.get('notify_period',
                                      default=[5, 20])

        self.scan_interval = cfg.get('scan_interval',
                                     default=60)

        self.agenda_times = cfg.get('agenda.times',
                                    default=['7:00', '12:00'])

        #self.agenda_horizon_future = cfg.get('agenda.horizon_future',
        #                                     default=2)

        self.horizon_unfinished = cfg.get('agenda.horizon_unfinished',
                                          default=24)
        self.horizon_incoming = cfg.get('agenda.horizon_incoming',
                                        default=720)

        self.list_unfinished_appointments = cfg.get('agenda.list_unfinished_appointments',
                                                    default=False)

        # Get template paths or calculate defaults
        self.agenda_path = cfg.get_path('agenda.agenda_template_path',
                                        required=False)

        self.notice_path = cfg.get_path('agenda.notice_template_path',
                                        required=False)

        self.agenda_path = helpers.get_default_template(self.agenda_path or 'agenda.txt.j2',
                                                        __file__)
        self.notice_path = helpers.get_default_template(self.notice_path or 'notice.txt.j2',
                                                        __file__)


    def register(self):
        self.calendar = Calendar(self.agenda_path)

        # Register calendar in global state - this is our public API
        self.state['calendar'] = self.calendar

        commands = [
            (['agenda', 'ag'], self.handle_agenda),
            (['search', 's'], self.handle_search),
        ]
        for aliases, callback in commands:
            self.assistant.command.register(aliases, callback)

    def handle_agenda(self, message):
        "Respond with an agenda on agenda command"
        agenda = self.get_agenda()
        log.debug("Sending agenda: %r", agenda)
        message.respond(agenda)

    def handle_search(self, message):
        """
        Enter an incremental search context
        """
        ctx = SearchContext(self.calendar)
        ctx.handler(message)
        return ctx

    def get_agenda(self):
        "Generate agenda"
        now = self.time.now()
        horizon_unfinished = now - dt.timedelta(hours=self.horizon_unfinished)
        horizon_incoming = now + dt.timedelta(hours=self.horizon_incoming)

        try:
            agenda = self.calendar.get_agenda(horizon_incoming,
                                              horizon_unfinished,
                                              self.list_unfinished_appointments,
                                              relative_to=now)
            return agenda
        except Exception:
            tb.print_exc()
            return "Error while rendering Agenda template."

    def send_agenda(self):
        "Used for sending periodically agenda"
        agenda = self.get_agenda()
        self.assistant.tell_boss(agenda)
