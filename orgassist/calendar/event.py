"""
Abstract events away from the org plugin so they can be used in other
modules and "agenda" handling can be shared.
"""
import datetime as dt
import jinja2

class EventState:
    """
    Different event sources can have different states. They are normally a
    short string which doesn't mean much. For eg. this can be: TODO, DONE,
    DELEGATED, CANCELLED.

    Some of those are considered DONE, other belong in an "Open" group and
    shoukd be listed in agendas.
    """
    def __init__(self, name, is_open=None):
        self.name = name
        if is_open is None:
            self.is_open = EventState.is_state_open(name)
        else:
            self.is_open = is_open

    @staticmethod
    def is_state_open(state):
        "Handle default states"
        open_map = {
            'TODO': True,
            'DELEGATED': True,
            'BLOCKED': True,
            'DONE': False,
            'CANCELLED': False,
        }
        try:
            return open_map[state]
        except KeyError:
            raise Exception("State %s has unknown default open/close state" % state)

    def __repr__(self):
        return '<EventState %s open=%s>' % (self.name,
                                            self.is_open)

class Event:
    """
    Abstracts a calendar event from plugins.
    """
    def __init__(self, headline, state=None):
        """Initialize event variables"""

        self.headline = headline

        # Set state
        self.set_state(state)

        self.tags = set()

        # A, B, C (letter)
        self.priority = None

        # The "most relevant date *now*".
        # 1) The next future day of the event (for example of a cyclic event)
        # 2) Or the closest "todays" date
        # 3) Last past date for unfinished/past events.
        self.relevant_date = None

        # Event can have multiple dates of various types.
        self.dates = []

        # Set of all date types for this event
        self.date_types = set()

        # Event body content
        self.body = ""

        # Metadata, eg. location in org-mode tree.
        # Controlled freely by creator.
        self.meta = {}

    def add_date(self, event_date, relative_to=None):
        "Add date to the event"
        assert event_date not in self.dates

        self.dates.append(event_date)

        # Update relevant date
        if self.relevant_date is None:
            self.relevant_date = event_date
        elif event_date.is_more_relevant(self.relevant_date,
                                         relative_to=relative_to):
            self.relevant_date = event_date

        # Update event type
        self.date_types.add(event_date.date_type)

    def set_state(self, state):
        "Handle state as object or string - if string, cast to object"
        if isinstance(state, str):
            self.state = EventState(state)
        else:
            self.state = state

    def add_tags(self, tags):
        "Add tags to the event"
        if isinstance(tags, str):
            tags = {tags}
        self.tags.update(tags)
        return self

    def format_notice(self, template_content):
        """
        Render a notice about this event using given template.

        If you are authoring a plugin which has weird additional metadata you
        can override this method.
        """
        # Jinja context
        now = dt.datetime.now()

        # Calculate time delta in conscise human-readable way
        delta_s = (self.relevant_date.sort_date - now).total_seconds()

        delta_h = delta_s // 60 // 60
        delta_s -= delta_h * 60 * 60

        delta_m = delta_s // 60
        delta_s -= delta_m * 60

        # If scheduler gets late 10 seconds - round the number.
        if delta_s > 50:
            delta_m += 1
            delta_s = 0

        delta_str = '%dh' % delta_h if delta_h > 0 else ''
        delta_str += '%dm' % delta_m if delta_m > 0 or delta_h > 0 else ''

        ctx = {
            'now': now,
            'event': self,
            'delta_str': delta_str,

            # Shortcuts
            'headline': self.headline,
            'relevant_date': self.relevant_date,
            'date': self.relevant_date.sort_date,
            # To differentiate template based on event subclasses
            'event_cls': self.__class__.__name__,
        }

        if template_content is None:
            return ctx

        template = jinja2.Template(template_content)
        rendered = template.render(ctx)

        return rendered

    def __repr__(self):
        "Useful debugging representation"
        add_up = [
            field if isinstance(field, str) else repr(field)
            for field in [
                "'" + self.headline[:20] + "'",
                self.priority,
                ('state=' + self.state.name) if self.state is not None else '',
                self.relevant_date,
                ','.join(self.tags),
            ]
            if field is not None
        ]
        return "<Event %s>" % " ".join(add_up)

    def __lt__(self, other):
        return self.relevant_date < other.relevant_date
