"""
Helper functions to orgnode to handle incoming events and appointments in
org-mode.

Originally: Parse org-mode agendas, task lists, etc. and return simple
reminders to be included in environment status bar or shell.
"""

import re
import datetime as dt
import traceback as tb
import os
from collections import defaultdict

from orgassist import log
from orgassist.calendar import Event, EventState
from orgassist.calendar import EventDate, DateType

from . import orgnode

def unindent(body):
    "Unindent a 'common indent' of body of text"
    lines = body.split('\n')

    if not lines:
        return body

    # Find possible indent in the first line
    m = re.match('^([ \t]+)', lines[0])
    if not m:
        # No ident found
        return body
    indent = m.group()

    # Find a smallest common indent in all lines (spaces/tabs mixed)
    for line in lines[1:]:
        if not line.strip():
            # Ignore lines without a text
            continue

        for i, char in enumerate(indent):
            if len(line) == i or char != line[i]:
                # Cut indent short
                indent = indent[:i]
                break

    # Strip indent
    unindented = [
        line.replace(indent, '', 1).rstrip()
        for line in lines
    ]

    # Strip empty lines from beginning and end.
    while unindented and not unindented[0].strip():
        unindented = unindented[1:]

    while unindented and not unindented[-1].strip():
        unindented = unindented[:-1]

    return "\n".join(unindented)


def load_orgnode(cfg):
    "Load data from all org-files using orgnode"
    # Aggregated Orgnodes objects
    db = []

    todo_all = set(cfg['todos_open'])
    todo_all.update(cfg['todos_closed'])
    todo_all.add(cfg['project'])

    for path in cfg['files']:
        db += orgnode.makelist(path, todo_default=todo_all)

    if not cfg['files_re']:
        return db

    first = True
    # Read by regexp
    regexp = re.compile(cfg['files_re'], flags=re.UNICODE)
    for root, dirs, files in os.walk(cfg['base'],
                                     followlinks=True):
        if '.git' in dirs:
            dirs.remove('.git')

        for filename in files:
            if not re.match(regexp, filename):
                continue

            path = os.path.join(root, filename)
            try:
                db += orgnode.makelist(path,
                                       todo_default=todo_all)
            except Exception:
                if cfg['resilient']:
                    log.warning("Warning: Ignoring error while parsing %s", path)
                    if first:
                        tb.print_exc()
                    first = False
                    continue
                raise

    return db

def orgnode_to_event(node, org_config, relative_to=None):
    "Convert orgnode entries to events"
    event = Event(node.headline)
    event.add_tags(node.tags)

    event.body = unindent(node.body)
    if node.todo:
        state = EventState(node.todo,
                           is_open=node.todo in org_config['todos_open'])
        event.set_state(state)
    if node.priority:
        event.priority = node.priority

    if node.scheduled:
        date = EventDate(node.scheduled, DateType.SCHEDULED)
        event.add_date(date, relative_to)

    if node.deadline:
        date = EventDate(node.deadline, DateType.DEADLINE)
        event.add_date(date, relative_to)

    for ranged in node.rangelist:
        date = EventDate(ranged, DateType.RANGE)
        event.add_date(date, relative_to)

    for node_date in node.datelist:
        # Appointment dates
        date = EventDate(node_date, DateType.TIMESTAMP)
        event.add_date(date, relative_to)

    return event


"""
def until(date, relative):
    "
    Return time difference taking into account that date might not have a time given.
    If so - assume end of day. `relative' always has a time.
    "

    # Decorate with time
    if not isinstance(date, dt.datetime):
        date = dt.datetime(date.year, date.month, date.day, 23, 59, 59)
        appointment = False
    else:
        # Appointment is an event with accurate time defined.
        appointment = True

    delta = (date - relative).total_seconds()
    # If negative - then a past event.
    return date, delta / 60.0 / 60.0 / 24.0, appointment


def closest(date_list, relative):
    "Find closest future event relative to a given date"
    # Closest date - original
    closest_date = None

    # Closest date converted to datetime
    closest_converted_date = None

    # Time delta for closest date
    closest_delta = None

    # Is the date an appointment? (accurate to hour:minute?)
    appointment = None

    for date in sorted(date_list):
        converted_date, days, appointment = until(date, relative)

        closest_date = date
        closest_converted_date = converted_date
        closest_delta = days

        if closest_delta < 0:
            # Past event, iterate more
            continue
        # This is a first future event, do not check more.
        break

    return {
        'converted_date': closest_converted_date,
        'date': closest_date,
        'delta': closest_delta,
        'appointment': appointment
    }

def get_totals_stat(db, cfg):
    "
    Count all entries versus not ignored (opened).

    This is supposed to help push TODOs without a specified execution time.
    "
    count_total = 0
    count_open = 0

    for entry in db:
        # Iterate over entries

        if not entry.todo:
            # No designation at all, not a `task'
            continue

        if (entry.datelist or entry.scheduled or
            entry.deadline or entry.rangelist):
            # Has time - is already counted elsewhere
            continue

        count_total += 1

        # Ignore ones marked as "done/finished/closed"
        if entry.todo not in cfg['todos_closed']:
            count_open += 1

    return count_open, count_total

"""

def get_incoming(db, cfg):
    """
    Parse all events and gather ones happening in the near
    future (set by horizont) and unfinished from past.

    Takes into account any possible dates, can report the same
    event multiple times for different dates.
    """
    today = dt.datetime.today()

    # Returned aggregation
    ret = {
        # Incoming events
        'incoming': [],

        # Past TODO events (SCHEDULED, DEADLINE) not marked as DONE
        'unfinished': [],

        # Things to show, to remind you, you're responsible
        # project entry -> {stats}
        'projects': {},

        # Found, but over-horizon
        'filtered_future': 0,
        'filtered_past': 0,
    }

    for entry in db:
        # Iterate over entries
        if entry.todo and entry.parent in ret['projects']:
            # Count number of tasks open within a project.
            # DONE, TODO, all types
            current_entry = entry
            while current_entry.parent:
                current_entry = current_entry.parent
                if current_entry in ret['projects']:
                    ret['projects'][current_entry][entry.todo] += 1

        # Now, ignore ones marked as "done/finished/closed"
        if entry.todo in cfg['todos_closed']:
            continue

        def analyze_dates(event, dates, datetype):
            data = closest(dates, relative=today)

            data.update({
                'eventtype': datetype,
                'headline': entry.headline,
                'body': unindent(entry.body),

                'entry': entry,
            })

            if data['delta'] is None:
                return # No dates, no event.
            elif data['delta'] < 0:
                # Past event
                if (cfg['horizont_past'] is not None and
                    data['delta'] >= -cfg['horizont_past']):

                    ret['unfinished'].append((data['converted_date'], data))
                else:
                    ret['filtered_past'] += 1
            else:
                # Future event
                if data['delta'] <= cfg['horizont_future']:
                    ret['incoming'].append((data['converted_date'], data))
                else:
                    ret['filtered_future'] += 1

        event = calendar.Event(entry.headline)
        event.body = unindent(entry.body)
        event.add_tags(entry.tags)

        analyze_dates(event, entry.datelist, 'TIMESTAMP')

        if entry.rangelist:
            starts = [dr[0] for dr in entry.rangelist]
            analyze_dates(event, starts, 'RANGE')

        scheduled = entry.scheduled
        deadline = entry.deadline

        if scheduled:
            analyze_dates(event, [scheduled], "SCHEDULED")

        if deadline:
            analyze_dates(event, [deadline], "DEADLINE")

        if entry.todo == cfg['project']:
            ret['projects'][entry] = defaultdict(lambda: 0)

    return ret
