"""
Console based reporting for data returned by orghelpers.

(C) Tomasz bla Fortuna
"""
import datetime as dt

def _get_marker(eventtype):
    if eventtype == 'DEADLINE':
        marker = 'D'
    elif eventtype == 'SCHEDULED':
        marker = 'S'
    elif eventtype == 'RANGE':
        marker = 'R'
    else:
        marker = ' '
    return marker


def _get_delta(delta, accurate=False):
    import math
    days = int(math.floor(delta))
    if days == 0:
        # Today
        if accurate:
            hours = math.floor(delta*24)
            if hours <= 0.1:
                return "NOW"
            if hours == 1:
                return "today in " + str(int(hours)) + " hour"
            if hours > 1:
                return "today in " + str(int(hours)) + " hours"
        else:
            return "today"
    elif days > 1:
        return "in " + str(days) + " days"
    elif days < 0:
        return str(-days) + " days ago"
    elif days == 1:
        return "1 day"


def report_stat(incoming_list, tasks_open, tasks_all):
    "Create a simple statistic for following days"
    incoming_list.sort()

    now = dt.datetime.now()
    eo_today = dt.datetime(now.year, now.month, now.day, 23, 59, 59)
    eo_tomorrow = eo_today + dt.timedelta(days=1)

    counted = set()

    stat_today = 0
    stat_tomorrow = 0
    stat_total = 0

    for incoming in incoming_list:
        closest_converted_date, data = incoming
        if data['entry'] in counted:
            continue # Count once, earliest entry
        counted.add(data['entry'])

        if closest_converted_date <= eo_today:
            stat_today += 1
        elif closest_converted_date <= eo_tomorrow:
            stat_tomorrow += 1

        stat_total += 1

    stat_rest = stat_total - stat_today - stat_tomorrow

    s = ""
    if stat_today:
        s += str(stat_today)
    if stat_tomorrow:
        s += '->%d' % stat_tomorrow
    if stat_rest:
        s += '-->%d' % stat_rest

    #s = "T %d->%d-->%d" % (stat_today, stat_tomorrow, stat_rest)

    # Not timed
    s += " %d/%d" % (tasks_open, tasks_all)
    return s


def report_incoming(incoming_list, cfg):
    "Report incoming tasks for following days"
    if not incoming_list:
        return

    today = dt.datetime.today()
    incoming_list.sort()
    add_separator = False # Today separator

    if incoming_list[0][0].day == today.day:
        add_separator = True

    for incoming in incoming_list:
        closest_converted_date, data = incoming
        todo = data['entry'].todo or 'TASK'

        if add_separator and closest_converted_date.day != today.day:
            add_separator = False
            print("- EOD -")

        marker = _get_marker(data['eventtype'])
        accurate = data['converted_date'] == data['date']
        # If equal - then the event has a time specified.
        if accurate and data['delta']*24 < cfg['mark_in']:
            marker += '--> '
        else:
            marker += '    '

        s = "%s %9s %-20s %s"
        s = s % (marker, todo, _get_delta(data['delta'], accurate),
                 data['entry'].headline[:60])
        print(s)


def report_unfinished(unfinished_list, cfg):
    "Report incoming tasks for following days"
    if not unfinished_list:
        return

    unfinished_list.sort()
    output = False

    for unfinished in unfinished_list:
        closest_converted_date, data = unfinished
        todo = data['entry'].todo

        if data['eventtype'] not in ['SCHEDULED', 'DEADLINE']:
            continue # Don't show things with plain timestamps

        marker = _get_marker(data['eventtype'])
        marker += ' DUE'
        accurate = data['converted_date'] == data['date']

        s = "%s %9s %-20s %s"
        s = s % (marker, todo, _get_delta(data['delta'], accurate),
                 data['entry'].headline[:60])

        output = True
        print(s)
    return output


def report_projects(projects):
    "Report an open projects you're responsible for"
    if not projects:
        return

    print("PROJECTS:")
    for project, stat in projects.items():
        print("  %-30s" % project.headline[:50], end=' ')
        stats = " ".join(["%s=%d" % (k, v) for k, v in stat.items()])
        if stats:
            print("(%s)" % stats)
        else:
            print()
    print()
