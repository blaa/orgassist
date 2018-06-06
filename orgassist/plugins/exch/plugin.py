"""
Exchange calendar integration.
"""

import datetime as dt
from collections import namedtuple

from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin
from orgassist.config import ConfigError

from orgassist.calendar import Event
from orgassist.calendar import EventDate, DateType

Attendee = namedtuple('Attendee', 'name, email, required')

@Assistant.plugin('exch')
class ExchPlugin(AssistantPlugin):
    """
    Exchange calendar integration. Reads events for today and in the given
    horizon and feeds them into the calendar core plugin.

    Will handle notifications and todays agenda display.
    """

    def validate_config(self):
        "Get all config values and test optional module existence."
        # Load optional modules only when module is configured.
        # Test here early that they exists.
        try:
            # pylint: disable=unused-variable
            from pyexchange import Exchange2010Service
            from pyexchange import ExchangeNTLMAuthConnection
        except ImportError:
            msg = ("Exchange Plugin requires an optional pyexchange module. "
                   "Install it with pip3 install pyexchange.")
            raise ConfigError(msg)

        self.username = self.config.get('username', assert_type=str)
        self.password = self.config.get('password', assert_type=str)
        self.url = self.config.get('url', assert_type=str)
        self.ca_path = self.config.get_path('ca_path', required=False)

        self.horizon_incoming = self.config.get('horizon_incoming',
                                                default=24,
                                                assert_type=int)

        self.my_email = self.config.get('my_email', default='',
                                        assert_type=str)

    def register(self):
        "Register commands"
        commands = [
            (['exch.refresh'], self.handle_refresh),
        ]
        for aliases, callback in commands:
            self.assistant.command.register(aliases, callback)

    def initialize(self):
        """
        Initialize connection and schedule periodic events.
        """
        # Loading optional modules only when module is configured.
        from pyexchange import Exchange2010Service
        from pyexchange import ExchangeNTLMAuthConnection

        self.connection = ExchangeNTLMAuthConnection(url=self.url,
                                                     username=self.username,
                                                     password=self.password)
        self.service = Exchange2010Service(self.connection)
        self.exch_calendar = self.service.calendar()
        self.connection.build_session()

        if self.ca_path is not None:
            self.connection.session.verify = self.ca_path

        # Initial refresh
        self.refresh_events()
        self.scheduler.every(60 * 10).seconds.do(self.refresh_events)

    def handle_refresh(self, message):
        "Handle force-refreshing and return stats on events"
        events = self.refresh_events()
        reply = "Read %d events from your calendar." % (len(events))
        message.respond(reply)

    def convert_event(self, exch_event):
        "Convert Exchange event to orgassist calendar event"
        # Drop external objects, gather all required data.
        # Don't leak abstraction.
        ctx = {
            'subject': exch_event.subject,
            'text_body': exch_event.text_body,
            'location': exch_event.location,
            'date_start': self.time.normalize(exch_event.start),
            'date_end': self.time.normalize(exch_event.end),
            'date_all_day': exch_event.is_all_day,

            'organizer': Attendee(name=exch_event.organizer.name,
                                  email=exch_event.organizer.email,
                                  required=True) if exch_event.organizer else None,
            'attendees': [
                Attendee(name=a.name,
                         email=a.email,
                         required=a.required)
                for a in exch_event.attendees
                if a is not None
            ],

            'your_meeting': False,
            'you_required': False,
        }

        # Safely determine organizer
        if ctx['organizer'] is None:
            ctx['organizer'] = Attendee(name='unknown',
                                        email='none',
                                        required=True)

        if ctx['organizer'].email == self.my_email:
            ctx['your_meeting'] = True

        myself = [
            a
            for a in ctx['attendees']
            if a.email == self.my_email
        ]

        if myself and myself[0].required:
            ctx['you_required'] = True

        # Context ready - construct our event
        parts = []
        if ctx['location']:
            parts.append('[' + ctx['location'] +  ']')

        priority = 'C'
        if ctx['your_meeting']:
            parts.append('Your meeting')
            priority = 'A'
        elif ctx['you_required']:
            parts.append("Required by %s for" % ctx['organizer'].name)
            priority = 'B'
        elif not ctx['you_required']:
            parts.append("Informed by %s about" % ctx['organizer'].name)

        parts.append('"' + ctx['subject'] + '"')
        parts.append("(%d attending)" % len(ctx['attendees']))

        headline = " ".join(parts)

        event = Event(headline)
        event.priority = priority

        event.body = ctx['text_body']
        event.meta['exch'] = ctx

        date = EventDate((ctx['date_start'], ctx['date_end']),
                         DateType.RANGE)
        event.add_date(date)

        return event

    def refresh_events(self):
        """
        Read events from exchange, convert and update calendar.
        """
        log.info("Periodic operation executed")

        now = self.time.now()

        start_of_day = now.replace(hour=0, minute=0)
        horizon_end = now + dt.timedelta(hours=self.horizon_incoming)

        try:
            events = self.exch_calendar.list_events(
                start=start_of_day,
                end=horizon_end,
                details=True
            )
        except AttributeError:
            # Module is badly written. In case of connection errors it
            # throws Attribute Error. Show error in case something weird
            # happened, but don't kill bot.
            log.exception("Connection (probably) error within exch module.")
            return None

        calendar_events = []
        for event in events.events:
            converted = self.convert_event(event)
            calendar_events.append(converted)

        log.info('Read %d events from exchange',
                 len(calendar_events))

        # Use shared state to talk to core plugins
        self.state['calendar'].update_events(calendar_events, 'exch')
        return calendar_events
