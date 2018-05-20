"""
The main plugin - org-mode plugin.

- Sent notifications before events
- Remind automatically about your todays agenda.
- Allow note-taking on the go.

Currently uses orgnode, later it might be sensible to use something newer.
Works for me though.

(C) 2018 by Tomasz bla Fortuna
"""

from orgassist import Assistant
from orgassist import log
from orgassist.assistant import AssistantPlugin


def load_org(cfg):
    "Bridge plugin with orgnode helpers"
    from orgassist.orgnode import orghelpers
    org_cfg = {
        # Include those files (full path)
        'files': cfg.get('files', default=[]),

        # Scan given base for all files matching regexp
        'files_re': cfg.get('org_regexp', default=r'.*\.org$'),
        'base': cfg.get_path('directory'),

        # Look 5 days ahead
        'horizont_future': cfg.get('agenda.horizont_future', default=2),
        'horizont_past': cfg.get('agenda.horizont_past', default=10),

        'todos_open': cfg.get('todos.open', default=['TODO']),
        'todos_closed': cfg.get('todos.closed', default=['DONE', "CANCELLED"]),

        # How grouping entry is marked - which groups TODOs and DONEs.
        'project': cfg.get('todos.project', default='PROJECT'),

        # Ignore exceptions during file parsing (happens in orgnode when file is
        # badly broken or not ORG at all)
        'resilient': False,
    }

    db = orghelpers.load_data(org_cfg)
    aggr = orghelpers.get_incoming(db, org_cfg)
    log.info('Refreshed/read org-mode data')
    return aggr, db


@Assistant.plugin('org')
class OrgPlugin(AssistantPlugin):
    """
    Handle operations on an org-mode tree
    """

    def refresh_db(self):
        "Refresh/load DB with org entries"
        aggr, _ = load_org(self.config)
        self.state['db'] = aggr


    def initialize(self):
        self.refresh_db()

    def register(self):
        commands = [
            (['agenda', 'ag'], self.handle_agenda),
        ]
        for aliases, callback in commands:
            self.assistant.register_command(aliases, callback)

    def handle_agenda(self, message):
        "Respond with an agenda on agenda command"
        message.respond('That is an agenda!')
        message.respond('It works!')
