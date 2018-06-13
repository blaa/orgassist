"""
"""

from orgassist.assistant import CommandContext

class SearchContext(CommandContext):
    """
    Keep context of an incremental search
    """

    def __init__(self, calendar, *args, **kwargs):
        """
        """
        # Copy current events
        self.events = calendar.events[:]

        # Search stat
        self.stat_kept = len(self.events)
        self.stat_dropped = 0

        # List of all partial queries
        self.queries = []
        super().__init__(*args, **kwargs)

    def narrow_down(self, new_query):
        "Narrow search down"
        matching = []
        kept, dropped = 0, 0
        new_query = new_query.lower()
        for event in self.events:
            txt = ' '.join([event.headline.lower(),
                            event.body.lower()])
            if new_query in txt:
                matching.append(event)
                kept += 1
            else:
                dropped += 1

        self.stat_dropped += dropped
        self.stat_kept -= dropped

        self.events = matching
        return kept, dropped

    def handler(self, message):
        "Narrow search with each query"
        query = message.text
        is_first = self.queries == []

        self.queries.append(query)
        _, dropped = self.narrow_down(query)
        full_query = " ".join(self.queries)

        if self.stat_kept == 0:
            message.respond("'{}' not found - closing search.".format(full_query))
            # Quit context
            return True

        # Summarize search
        if not is_first:
            msg = "{} dropped, {} matches for '{}':".format(dropped, self.stat_kept,
                                                            full_query)
        else:
            msg = "{} matches for '{}':".format(self.stat_kept, full_query)
        message.respond(msg)

        # TODO: Parametrize count, trim and strings
        for i, event in enumerate(self.events[:10]):
            state = event.state.name + ' ' if event.state else ''
            msg = "{:2d}. {}{}".format(i+1, state, event.headline)
            message.respond(msg)
            if len(event.body) > 200:
                message.respond("   " + event.body[:200] + "...")
            elif event.body:
                message.respond("   " + event.body)

        return False

    def describe(self):
        return "Search for: " + " ".join(self.queries)
