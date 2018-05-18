import random
import io
import datetime as dt

import unittest

import jinja2

from orgassist.calendar import DateType
from . import orgnode
from . import helpers

# Example Org file for testing
# pre-generated to have a todays dates.
ORG_TMPL = """
* PROJECT Aggregator
** TODO This is open task   :OPEN_TASK:
   SCHEDULED: <{{ today }}>
** TODO Past task           :TAG1:
   SCHEDULED: <{{ yesterday }}>
** DONE Already done        :DEADLINE:
   DEADLINE: <{{ today }}>
** [#B] Appointment         :APP:
   <{{ accurate }}>
** Whole day event          :WHOLE_DAY:
   <{{ today }}>
** Inactive date            :INACTIVE:
   [{{ accurate }}]
** [#A] Ranged              :RANGE:
   <{{ yesterday }}>--<{{ today }}>
"""
DAYTIME = '%Y-%m-%d %a %H:%M'
DAY = '%Y-%m-%d %a'

# For testing org helpers
ORG_CONFIG = {
    'files': [],

    'files_re': None,
    'base': None,

    'todos_open': ['TODO'],
    'todos_closed': ['DONE', 'CANCELLED'],

    # How grouping entry is marked - which groups TODOs and DONEs.
    'project': 'PROJECT',

    'resilient': False,
}

class TestOrg(unittest.TestCase):
    "Test org mode reading"

    def setUp(self):
        today = dt.datetime.now().replace(hour=random.randint(6, 10),
                                          minute=random.randint(0, 59))

        yesterday = today - dt.timedelta(days=1)
        tomorrow = today + dt.timedelta(days=1)
        accurate = today + dt.timedelta(hours=3)

        context = {
            'today': today.strftime(DAY),
            'yesterday': yesterday.strftime(DAY),
            'tomorrow': tomorrow.strftime(DAY),
            'accurate': accurate.strftime(DAYTIME),
        }

        tmpl = jinja2.Template(ORG_TMPL)

        self.rendered_org = tmpl.render(context)
        self.org_file = io.StringIO(self.rendered_org)
        self.db = orgnode.makelist(self.org_file,
                                   todo_default=['TODO', 'DONE', 'PROJECT'])


    def test_orgnode(self):
        "Test reading ORG using orgnode"
        self.assertIn('OPEN_TASK', self.db[1].tags)
        self.assertEqual(self.db[1].headline, 'This is open task')

    def test_conversion(self):
        "Test orgnode to events conversion"
        events = [
            helpers.orgnode_to_event(node, ORG_CONFIG)
            for node in self.db
        ]

        # If something fails intermittently - show debug data
        print(self.rendered_org)

        # Validate assumptions
        for event in events:
            print(event)

            if 'RANGE' in event.tags:
                self.assertEqual(event.priority, 'A')
                self.assertIn(DateType.RANGE, event.date_types)
                self.assertEqual(event.relevant_date.date_type,
                                 DateType.RANGE)
            if 'OPEN_TASK' in event.tags:
                self.assertEqual(event.priority, None)
                self.assertEqual(event.state.name, 'TODO')
                self.assertTrue(event.state.is_open)
                self.assertIn(DateType.SCHEDULED, event.date_types)
                self.assertEqual(event.relevant_date.date_type,
                                 DateType.SCHEDULED)
            if 'DEADLINE' in event.tags:
                relevant = event.relevant_date
                self.assertEqual(event.state.name, 'DONE')
                self.assertFalse(event.state.is_open)
                self.assertEqual(relevant.date_type,
                                 DateType.DEADLINE)
                self.assertFalse(relevant.appointment)
            if 'APP' in event.tags:
                relevant = event.relevant_date

                self.assertEqual(event.priority, 'B')
                self.assertTrue(relevant.appointment)

        self.assertEqual(len(events), 8)


