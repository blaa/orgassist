"""
Org-mode compatible calendar implementation - handles a number of events in
time.
"""
import datetime as dt
import jinja2

from orgassist import log

class Calendar:
    """
    Manages multiple events, generates agenda
    """
    def __init__(self, agenda_path=None, agenda_content=None):
        "Initialize calendar"

        # Events sorted by sort_date
        self.events = []

        # Path to agenda
        self.agenda_path = agenda_path
        self.agenda_content = agenda_content
        assert self.agenda_content != self.agenda_path

    def add_events(self, events, internal_tag=None):
        "Add new events to the calendar"
        for event in events:
            event.meta['calendar_tag'] = internal_tag
        self.events += events
        self.events.sort()

    def del_events(self, internal_tag=None):
        "Delete events by internal tag"
        if internal_tag is None:
            self.events = []

        else:
            self.events = [
                event
                for event in self.events
                if event.meta['calendar_tag'] != internal_tag
            ]

    def get_unfinished(self, horizon, relative_to=None):
        """
        Get a list of past unfinished events

        Args:
          horizon (datetime): The oldest date to consider.
        """
        if relative_to is None:
            relative_to = dt.datetime.now()

        print("GET UNFINISHED")
        unfinished = []
        for event in self.events:
            print("  ", event)
            date = event.relevant_date.sort_date
            if date < horizon:
                print("  BEFORE HORIZON")
                continue
            if event.state is not None and not event.state.is_open:
                print("  NOT OPEN STATE")
                continue
            if date > relative_to:
                # We are in future - not unfinished.
                break

            print("  GOT YOU")
            unfinished.append(event)
        return unfinished

    def get_incoming(self, horizon, relative_to=None):
        "Get a list of scheduled and planned events"
        incoming = []
        if relative_to is None:
            relative_to = dt.datetime.now()

        print("GET INCOMING")
        incoming = []
        for event in self.events:
            date = event.relevant_date.sort_date
            print("  ", event)
            if date < relative_to:
                print("    IN PAST")
                continue
            if date > horizon:
                print("    OVER HORIZON")
                break

            # State doesn't matter as long as the date is accurate
            if not event.relevant_date.appointment:
                continue

            print("  GOT YOU")
            incoming.append(event)
        return incoming

    def get_scheduled(self, horizon, relative_to=None):
        "Get tasks scheduled or deadlining in given period"
        if relative_to is None:
            relative_to = dt.datetime.now()

        print("GET SCHEDULED")
        scheduled = []
        for event in self.events:
            date = event.relevant_date.sort_date
            print("  ", event)
            if date < relative_to:
                print("    IN PAST")
                continue
            if date > horizon:
                print("    OVER HORIZON")
                break

            # State doesn't matter as long as the date is accurate
            if not event.relevant_date.appointment:
                continue

            print("  GOT YOU")
            scheduled.append(event)

        return scheduled

    def get_agenda(self, horizon_incoming, horizon_unfinished, relative_to=None):
        "Generate agenda in a text format"

        log.info("Getting agenda from %r to %r",
                 horizon_unfinished, horizon_incoming)

        # Open and read when needed so the file can be updated
        # without restarting bot.
        if self.agenda_content is not None:
            assert self.agenda_path is None
            content = self.agenda_content
        else:
            assert self.agenda_path is not None
            with open(self.agenda_path, 'r') as handle:
                content = handle.read()
        template = jinja2.Template(content)

        ctx = {
            'unfinished': self.get_unfinished(horizon_unfinished,
                                              relative_to),
            'incoming': self.get_incoming(horizon_incoming, relative_to),
            'today': relative_to,
        }

        return template.render(ctx)

    def __repr__(self):
        txt = "<Calendar events=%d>"
        return txt % len(self.events)
