import unittest
import datetime as dt

from orgassist.helpers import EventDate, Event, DateType

class TestEvent(unittest.TestCase):
    """
    Test Event and EventDates helpers.
    """

    def test_dates(self):
        "Test event date creation"
        now = dt.datetime.now()

        # Test date creation
        appointment_in_hour = EventDate(now + dt.timedelta(hours=1),
                                        DateType.APPOINTMENT)

        deadline_in_hour = EventDate(now + dt.timedelta(hours=1),
                                     DateType.DEADLINE)

        appointment_in_3hours = EventDate(now + dt.timedelta(hours=3),
                                          DateType.APPOINTMENT)

        appointment_later = EventDate(now + dt.timedelta(days=2),
                                      DateType.APPOINTMENT)

        old_appointment = EventDate(now - dt.timedelta(days=2),
                                    DateType.APPOINTMENT)

        task_today = EventDate(now.date(),
                               DateType.SCHEDULED)

        deadline_yesterday = EventDate((now - dt.timedelta(days=1)).date(),
                                       DateType.SCHEDULED)

        start_date = now + dt.timedelta(minutes=10)
        end_date = now + dt.timedelta(days=3)
        ranged_date = EventDate((start_date, end_date),
                                DateType.RANGE)

        # Asserts on the API
        self.assertEqual(ranged_date.date, start_date)
        self.assertEqual(ranged_date.date_end, end_date)
        self.assertEqual(ranged_date.date_type, DateType.RANGE)
        self.assertTrue(ranged_date.appointment)

        self.assertTrue(appointment_in_3hours.appointment)
        self.assertFalse(task_today.appointment)

        # Check relevancy algorithm
        self.assertTrue(appointment_in_hour.is_more_relevant(appointment_in_3hours))
        self.assertTrue(appointment_in_hour.is_more_relevant(appointment_later))
        self.assertTrue(appointment_in_hour.is_more_relevant(task_today))
        self.assertFalse(task_today.is_more_relevant(appointment_in_hour))
        self.assertTrue(task_today.is_more_relevant(old_appointment))
        self.assertTrue(appointment_later.is_more_relevant(old_appointment))

        # Ranged starts earlier
        self.assertFalse(appointment_in_3hours.is_more_relevant(ranged_date,
                                                                relative_to=now))

        # Mixed thoughts on that. ;-)
        self.assertTrue(task_today.is_more_relevant(deadline_yesterday))
        self.assertTrue(deadline_in_hour.is_more_relevant(appointment_in_hour))

    def test_events(self):
        "Test event behaviour"

        headline = "This is an event headline!"
        event = Event(headline, state="TODO")

        # Asserts on API
        self.assertEqual(event.headline, headline)
        self.assertEqual(event.body, "")
        self.assertIsNone(event.relevant_date)

        # Schedule the event for today.
        now = dt.datetime.now()
        sched_date = EventDate(now.date(), DateType.SCHEDULED)
        event.add_date(sched_date)

        self.assertTrue(DateType.SCHEDULED in event.event_types)
        self.assertEqual(event.relevant_date, sched_date)

        # But when given another date:
        app_date = EventDate(now + dt.timedelta(hours=2),
                             DateType.APPOINTMENT)
        event.add_date(app_date)

        self.assertTrue(DateType.APPOINTMENT in event.event_types)
        self.assertEqual(event.relevant_date, app_date)

        # Order should change anything:
        event = Event(headline, state="TODO")
        event.add_date(app_date)
        event.add_date(sched_date)
        self.assertTrue(DateType.APPOINTMENT in event.event_types)
        self.assertEqual(event.relevant_date, app_date)

    def test_tags(self):
        "Test tags on event"

        headline = "This is an event headline!"
        event = Event(headline, state="TODO")
        event.add_tags(["TEST", "PRIVATE"])
        self.assertIn('TEST', event.tags)
