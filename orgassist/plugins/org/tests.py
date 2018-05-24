
import unittest
import datetime as dt
import jinja2
import random
import io

from orgassist import orgnode

# Example Org file for testing
# pre-generated to have a todays dates.
ORG_TMPL = """
* PROJECT Aggregator
** TODO This is open task   :TAG1:
   SCHEDULED: <{{ today }}>
** TODO Past task           :TAG1:
   SCHEDULED: <{{ yesterday }}>
** DONE Already done        :TAG2:
   SCHEDULED: <{{ today }}>
** Appointment
   SCHEDULED: <{{ accurate }}>
"""
DAYTIME = '%Y-%m-%d %a %H:%M'
DAY = '%Y-%m-%d %a'

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

    def test_orgnode(self):
        "Test reading ORG using orgnode"
        db = orgnode.makelist(self.org_file)

        self.assertIn('TAG1', db[1].tags)
        self.assertEqual(db[1].headline, 'This is open task')

        

