"""
The main plugin - org-mode plugin.

- Sent notifications before events
- Remind automatically about your todays agenda.
- Allow note-taking on the go.

Currently uses orgnode, later it might be sensible to use something newer.
Works for me though.

(C) 2018 by Tomasz bla Fortuna
"""
import datetime as dt
from orgassist import log
from orgassist.assistant import Assistant, AssistantPlugin
from orgassist.config import ConfigError

from . import helpers
from orgassist.helpers import get_template, get_default_template

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
        return events

    def register(self):
        commands = [
            (['note', 'no'], self.handle_note),
            (['refresh'], self.handle_refresh),
        ]
        for aliases, callback in commands:
            self.assistant.command.register(aliases, callback)

    def initialize(self):
        "Initialize org plugin, read database and schedule updates"
        self.refresh_db()

        interval = self.config.get('scan_interval_s', assert_type=int)
        self.scheduler.every(interval).seconds.do(self.refresh_db)

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

            # Hide body and headline of those - keep date.
            'tags_private': self.config.get('private_tags', default=[]),

            # How grouping entry is marked - which groups TODOs and DONEs.
            'project': self.config.get('todos.project', default='PROJECT'),

            # Ignore exceptions during file parsing (happens in orgnode when file is
            # badly broken or not ORG at all).
            # This should be fixed in orgnode.
            'resilient': False,
        }

        self.note_inbox = self.config.get_path('note.inbox',
                                               required=False)
        self.note_tag = self.config.get('note.tag',
                                        required=False)
        self.note_position = self.config.get('note.position',
                                             default='append')
        if self.note_position != 'append':
            raise ConfigError('Unhandled new note position: ' + self.note_position)
        try:
            open(self.note_inbox, 'a')
        except IOError:
            raise ConfigError("Unable to open note inbox file: " + self.note_inbox)

        path = self.config.get_path('note.template',
                                    required=False)
        self.new_note_path = get_default_template(path or 'new_note.txt.j2',
                                                  __file__)

        # Parse auto_schedule
        auto_schedule = self.config.get('note.auto_schedule',
                                        required=False)
        self.parse_auto_schedule(auto_schedule)

    def parse_auto_schedule(self, auto_schedule):
        "Parse auto schedule field"
        self.auto_schedule_day_mod = 0
        self.auto_schedule_time = (None, None)
        if isinstance(auto_schedule, str):
            self.auto_schedule = True
            tmp = auto_schedule.split(':', 1)
            mod_map = {
                'today': 0,
                'tomorrow': 1,
            }
            if len(tmp) == 1:
                day, hour, minutes = tmp[0], None, None
            else:
                # Day and hour
                try:
                    hour, minutes = [int(x) for x in tmp[1].split(':')]
                except ValueError:
                    raise ConfigError("Unable to parse hour in auto_schedule field")
                day = tmp[0]
            if tmp[0] not in mod_map:
                raise ConfigError("Unable to understand auto_schedule field")
            self.auto_schedule_day_mod = mod_map[day]
            self.auto_schedule_time = (hour, minutes)
        else:
            self.auto_schedule = False

    def handle_note(self, message):
        "Take a note"
        template = get_template(self.new_note_path, None)
        now = self.time.now()

        if self.auto_schedule:
            # Get schedule string
            schedule = now + dt.timedelta(days=self.auto_schedule_day_mod)
            if self.auto_schedule_time[0] is None:
                # TODO: How will %a behave in different locales? Is it needed?
                schedule = schedule.strftime("%Y-%m-%d %a")
            else:
                # Time!
                schedule = schedule.replace(hour=self.auto_schedule_time[0],
                                            minute=self.auto_schedule_time[1])
                if schedule < now:
                    # In past - move to "now" at least.
                    schedule = now
                schedule = schedule.strftime("%Y-%m-%d %a %H:%M")
        else:
            schedule = None

        ctx = {
            'now': now,
            'headline': message.text,
            'sender': message.sender,
            'schedule': schedule,
            'tag': ':' + self.note_tag + ':' if self.note_tag else None
        }
        snippet = template.render(ctx)

        with open(self.note_inbox, 'a') as handler:
            handler.write(snippet + '\n')

        if schedule:
            message.respond('Scheduled for ' + schedule)
        else:
            message.respond('Got it!')

    def handle_refresh(self, message):
        "Handle refresh request"
        events = self.refresh_db()
        message.respond("Loaded %d events" % len(events))

