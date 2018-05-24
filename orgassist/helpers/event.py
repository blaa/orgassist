import datetime as dt
import enum

class DateType(enum.Enum):
    """
    Different types of events

    Smaller values sort as "more" important in relevancy algorithm.
    """
    DEADLINE = enum.auto()
    APPOINTMENT = enum.auto()
    SCHEDULED = enum.auto()
    RANGE = enum.auto()

class EventDate:
    """
    Handle operations on a date, distinguishes different date types, date
    ranges and cyclic dates.
    """
    def __init__(self, date, date_type):
        # Date is an appointment if has hour and minutes.
        self.appointment = False

        # Handle ranges almost normally.
        if date_type == DateType.RANGE:
            assert isinstance(date, tuple)
            self.date, self.date_end = date
        else:
            self.date, self.date_end = date, None

        self.date_type = date_type
        assert date_type in DateType

        # Sortable version, always with a time.
        if not isinstance(self.date, dt.datetime):
            self.sort_date = dt.datetime(self.date.year,
                                         self.date.month,
                                         self.date.day,
                                         23, 59, 59)
        else:
            self.sort_date = self.date
            self.appointment = True

    def __le__(self, event_date):
        "Compare dates"
        return self.sort_date <= event_date.sort_date

    def is_more_relevant(self, other, relative_to=None):
        """
        Return true if self is more relevant than given date.

        relative_to defaults to "now" in the current timezone.

        Definition of the "most" relevant is in order of priority:
        - Todays appointment (accurate to minute date, today)
        - Todays date of: deadline, schedule, range start, end
        - Closest future "any" date.
        - Closest past "any" date.

        Algorithm:
        - Construct tuples:
          (-1 - future, 1 - past;
           absolute delta to now;
           date_type)
        - And use a "smaller" tuple.
        """
        if relative_to is None:
            relative_to = dt.datetime.now()

        # Future is positive
        delta_this = (self.sort_date - relative_to).total_seconds()
        delta_other = (other.sort_date - relative_to).total_seconds()

        this_tuple = (
            -1 if delta_this >= 0 else 1,
            abs(delta_this),
            self.date_type.value
        )

        other_tuple = (
            -1 if delta_other >= 0 else 1,
            abs(delta_other),
            other.date_type.value
        )

        """
        TODO: Remove when certain, the algorithm is ok.
        print("\nCOMPARE")
        print("  ", self, other)
        print("  ", delta_this, delta_other)
        print("  ", this_tuple, other_tuple)
        if this_tuple <= other_tuple:
            print("  THIS")
        else:
            print("  OTHER")
        """
        return this_tuple <= other_tuple

    def __repr__(self):
        "Display EventDates nicely"
        def format_date(date):
            "Short format for date"
            if isinstance(date, dt.datetime):
                return date.strftime("%Y-%m-%d %H:%M")
            return date.strftime("%Y-%m-%d")

        if self.date_type == DateType.RANGE:
            ranged = '<->[%s]' % format_date(self.date_end)
        else:
            ranged = ''
        txt = '<EventDate [%s]%s %s>' % (format_date(self.date), ranged,
                                         self.date_type.name)
        return txt

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

        # The "most relevant date today".
        # 1) The next future day of the event (for example of a cyclic event)
        # 2) Or the last "todays" date
        # 3) Last past date for unfinished/past events.
        self.relevant_date = None

        # Event can have multiple dates of various types.
        self.dates = []

        # Set of all date types for this event
        self.event_types = set()

        self.body = ""

    def add_date(self, event_date):
        "Add date to the event"
        assert event_date not in self.dates

        self.dates.append(event_date)

        # Update relevant date
        if self.relevant_date is None:
            self.relevant_date = event_date
        elif event_date.is_more_relevant(self.relevant_date):
            self.relevant_date = event_date

        # Update event type
        self.event_types.add(event_date.date_type)

    def add_tags(self, tags):
        if isinstance(tags, str):
            tags = {tags}
        self.tags.update(tags)
        return self
