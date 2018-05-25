"""
Abstract events away from the org plugin so they can be used in other
modules and "agenda" handling can be shared.
"""

class Event:
    """
    Abstracts a calendar event from plugins.
    """

    def __init__(self, headline, state=None):
        """Initialize event variables"""

        self.headline = headline
        # "TODO", "DONE", etc. Varies, hence not an enum.
        self.state = state
        self.tags = set()

        # A, B, C (letter)
        self.priority = None

        # The "most relevant date today".
        # 1) The next future day of the event (for example of a cyclic event)
        # 2) Or the last "todays" date
        # 3) Last past date for unfinished/past events.
        self.relevant_date = None

        # Event can have multiple dates of various types.
        self.dates = []

        # Set of all date types for this event
        self.date_types = set()

        self.body = ""

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

    def add_tags(self, tags):
        "Add tags to the event"
        if isinstance(tags, str):
            tags = {tags}
        self.tags.update(tags)
        return self
