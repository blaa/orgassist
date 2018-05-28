"""
The main plugin - org-mode plugin.

- Sent notifications before events
- Remind automatically about your todays agenda.
- Allow note-taking on the go.

Currently uses orgnode, later it might be sensible to use something newer.
Works for me though.

(C) 2018 by Tomasz bla Fortuna
"""
from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin

from . import helpers


@Assistant.plugin('org')
class OrgPlugin(AssistantPlugin):
    """
    Handle operations on an org-mode tree
    """
    def refresh_db(self):
        "Refresh/load DB with org entries"
        log.info('Refreshed/read org-mode data')
        db = helpers.load_orgnode(self.parsed_config)
        events = [
            helpers.orgnode_to_event(node, self.parsed_config)
            for node in db
        ]

        # TODO: Handle TODOs too, not only the appointments/schedules
        events = [
            event
            for event in events
            if event.relevant_date is not None
        ]

        self.state['calendar'].del_events('org')
        self.state['calendar'].add_events(events, 'org')


    def register(self):
        commands = [
            (['note', 'no'], self.handle_note),
        ]
        for aliases, callback in commands:
            self.assistant.register_command(aliases, callback)

    def initialize(self):
        "Initialize org plugin, read database and schedule updates"
        self.refresh_db()

        interval = self.config.get('scan_interval_s', assert_type=int)
        self.scheduler.every(interval).seconds.do(self.refresh_db)

        #self.scheduler.every(10).seconds.do(lambda:
        # self.assistant.tell_boss('You are a bad person.\nTesttest\ntesttest'))

    def validate_config(self):
        "Read config and apply defaults"
        self.parsed_config = {
            # Include those files (full path)
            'files': self.config.get('files', default=[]),

            # Scan given base for all files matching regexp
            'files_re': self.config.get('org_regexp', default=r'.*\.org$'),
            'base': self.config.get_path('directory'),

            # Look 5 days ahead
            #'horizont_future': self.config.get('agenda.horizont_future', default=2),
            #'horizont_past': self.config.get('agenda.horizont_past', default=10),

            'todos_open': self.config.get('todos.open', default=['TODO']),
            'todos_closed': self.config.get('todos.closed', default=['DONE', 'CANCELLED']),

            # How grouping entry is marked - which groups TODOs and DONEs.
            'project': self.config.get('todos.project', default='PROJECT'),

            # Ignore exceptions during file parsing (happens in orgnode when file is
            # badly broken or not ORG at all).
            # This should be fixed in orgnode.
            'resilient': False,
        }

    def handle_note(self, message):
        "Take a note"
        pass
