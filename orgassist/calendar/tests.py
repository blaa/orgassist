import unittest
import random
import datetime as dt

from orgassist.calendar import EventDate, Event, DateType
from orgassist.calendar import EventState
from orgassist.calendar import Calendar

class TestEvent(unittest.TestCase):
    """
    Test Event and EventDates helpers.
    """

    @staticmethod
    def day_starts():
        """
        Early day date.

        Test would fail without an early "now" date because appointments past
        midnight get less important than stuff scheduled for "today" (23:59).

        This relavancy system might work bad for people working graveyard
        shifts.
        """
        return dt.datetime.now().replace(hour=random.randint(6, 10),
                                         minute=random.randint(0, 59))

    def create_dates(self):
        "Shared dates. A bit of ugly code to have low number of repetitions"
        # pylint: disable=attribute-defined-outside-init,too-few-public-methods,too-many-instance-attributes
        class Dates:
            "Convenient date holder"
        dates = Dates()

        dates.now = self.day_starts()
        now = dates.now

        # Test date creation
        dates.appointment_in_hour = EventDate(now + dt.timedelta(hours=1),
                                              DateType.TIMESTAMP)

        dates.deadline_in_hour = EventDate(now + dt.timedelta(hours=1),
                                           DateType.DEADLINE)

        dates.appointment_in_3hours = EventDate(now + dt.timedelta(hours=3),
                                                DateType.TIMESTAMP)

        dates.appointment_later = EventDate(now + dt.timedelta(days=2),
                                            DateType.TIMESTAMP)

        dates.old_appointment = EventDate(now - dt.timedelta(days=2),
                                          DateType.TIMESTAMP)

        dates.task_today = EventDate(now.date(),
                                     DateType.SCHEDULED)

        dates.deadline_yesterday = EventDate((now - dt.timedelta(days=1)).date(),
                                             DateType.SCHEDULED)

        dates.start_date = now + dt.timedelta(minutes=10)
        dates.end_date = now + dt.timedelta(days=3)
        dates.ranged_date = EventDate((dates.start_date,
                                       dates.end_date),
                                      DateType.RANGE)
        return dates

    def test_dates(self):
        "Test event date creation"
        dates = self.create_dates()
        now = dates.now

        # Asserts on the API
        self.assertEqual(dates.ranged_date.date, dates.start_date)
        self.assertEqual(dates.ranged_date.date_end, dates.end_date)
        self.assertEqual(dates.ranged_date.date_type, DateType.RANGE)
        self.assertTrue(dates.ranged_date.appointment)

        self.assertTrue(dates.appointment_in_3hours.appointment)
        self.assertFalse(dates.task_today.appointment)

        # Check relevancy algorithm
        self.assertTrue(dates.appointment_in_hour.is_more_relevant(dates.appointment_in_3hours,
                                                                   relative_to=now))
        self.assertTrue(dates.appointment_in_hour.is_more_relevant(dates.appointment_later,
                                                                   relative_to=now))
        self.assertTrue(dates.appointment_in_hour.is_more_relevant(dates.task_today,
                                                                   relative_to=now))
        self.assertFalse(dates.task_today.is_more_relevant(dates.appointment_in_hour,
                                                           relative_to=now))
        self.assertTrue(dates.task_today.is_more_relevant(dates.old_appointment,
                                                          relative_to=now))
        self.assertTrue(dates.appointment_later.is_more_relevant(dates.old_appointment,
                                                                 relative_to=now))

        # Ranged starts earlier
        self.assertFalse(dates.appointment_in_3hours.is_more_relevant(dates.ranged_date,
                                                                      relative_to=now))

        # Mixed thoughts on that. ;-)
        self.assertTrue(dates.task_today.is_more_relevant(dates.deadline_yesterday,
                                                          relative_to=now))
        self.assertTrue(dates.deadline_in_hour.is_more_relevant(dates.appointment_in_hour,
                                                                relative_to=now))

    def test_events(self):
        "Test event behaviour"

        headline = "This is an event headline!"
        event = Event(headline, state="TODO")

        # Asserts on API
        self.assertEqual(event.headline, headline)
        self.assertEqual(event.body, "")
        self.assertIsNone(event.relevant_date)

        # Schedule the event for today.
        now = self.day_starts()
        sched_date = EventDate(now.date(), DateType.SCHEDULED)
        event.add_date(sched_date, relative_to=now)

        self.assertTrue(DateType.SCHEDULED in event.date_types)
        self.assertEqual(event.relevant_date, sched_date)

        # But when given another date:
        app_date = EventDate(now + dt.timedelta(hours=2),
                             DateType.TIMESTAMP)
        event.add_date(app_date, relative_to=now)

        self.assertTrue(DateType.TIMESTAMP in event.date_types)
        self.assertEqual(event.relevant_date, app_date)

        # Order should change anything:
        state = EventState("TODO")
        event = Event(headline, state=state)
        event.add_date(app_date, relative_to=now)
        event.add_date(sched_date, relative_to=now)
        self.assertTrue(DateType.TIMESTAMP in event.date_types)
        self.assertEqual(event.relevant_date, app_date)

    def test_tags(self):
        "Test tags on event"

        headline = "This is an event headline!"
        state = EventState("TODO")
        self.assertTrue(state.is_open)
        event = Event(headline, state=state)
        event.add_tags(["TEST", "PRIVATE"])
        self.assertIn('TEST', event.tags)

    def test_calendar(self):
        "Test calendar behaviour"
        dates = self.create_dates()
        events = []
        for name, value in dates.__dict__.items():
            if isinstance(value, EventDate):
                event = Event(name)
                event.add_date(value)
                events.append(event)

        horizon_incoming = dates.now.replace(hour=23, minute=59, second=59)
        horizon_unfinished = dates.now - dt.timedelta(days=2)

        agenda_template = """
        {% for task in unfinished %}
         Unfinished:{{ task }}
        {% endfor %}
        {% for task in incoming %}
         Incoming:{{ task }}
        {% endfor %}
        """

        calendar = Calendar(agenda_content=agenda_template)
        calendar.add_events(events, internal_tag='org')

        unfinished = calendar.get_unfinished(horizon_unfinished, relative_to=dates.now)
        scheduled = calendar.get_scheduled(horizon_incoming, relative_to=dates.now)
        agenda = calendar.get_agenda(horizon_incoming=horizon_incoming,
                                     horizon_unfinished=horizon_unfinished)

        print("AGENDA:", type(agenda), agenda, "END")
        self.assertGreaterEqual(len(unfinished), 2)
        #self.assertGreaterEqual(len(scheduled), 0)
        #self.assertGreaterEqual(len(agenda.split('\n')), 5)
