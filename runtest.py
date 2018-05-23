#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate examplare report out of org-mode.
(C) Tomasz bla Fortuna
"""

from orgassist.orgnode import orghelpers, orgreports

##
# Config
CFG = {
    # Include those files (full path)
    'files': [],

    # Scan given base for all files matching regexp
    'files_re': r'.*\.org$',
    'base': "/home/bla/.org/",

    # Look 5 days ahead
    'horizont_future': 5.0,
    'horizont_past': 50.0,

    # Mark tasks with time, happening in less than X hours
    'mark_in': 3.0,

    'todos_open': ["TODO", "DELEGATED"],
    'todos_closed': ["DONE", "CANCELLED", "DEFERRED"],

    # How grouping entry is marked - which groups TODOs and DONEs.
    'project': 'PROJECT',

    # Ignore exceptions during file parsing (happens in orgnode when file is
    # badly broken or not ORG at all)
    'resilient': False,
}

def test_report(incoming, unfinished, cfg):
    """
    Report incoming tasks for following days

    Constructing a single day (almost) report for assistant.

    1) Appointments today: (any with direct hour)
    - @hh:mm ....
    - @hh:mm ....

    2) Scheduled for today: (without direct hour)
    ... + mark deadlines in a specific way.

    3) Stuff Due: (scheduled, not marked as DONE)
    ...should have been done...

    """
    import datetime as dt

    if not incoming:
        return

    print()
    print("TESTING")

    txt = []

    incoming.sort()

    apps = [
        event
        for _, event in incoming
        if event['appointment'] is True
    ]

    planned = [
        event
        for _, event in incoming
        if event['appointment'] is False
    ]

    if apps:
        txt.append("You have following appointments today:")
        for app in apps:
            when = app['date'].strftime("%H:%m")
            #txt.append(repr(app))
            type_msg_map = {
                'SCHEDULED': "at {} you scheduled '{}'",
                'TIMESTAMP': "at {} you have an appointment '{}'",
                'RANGE': "at {} a long event starts '{}'",
                'DEADLINE': "at {} you reach DEADLINE of {}"
            }
            msg = type_msg_map[app['eventtype']]
            txt.append(msg.format(when, app['headline']))


    if planned:
        txt.append("You planned for today:")
        for task in planned:
            txt.append(repr(task))

    output = "\n".join(txt)
    print("REPORT\n", output, "\nEND OF REPORT")



def main():
    u"Display raport and save statistics"
    db = orghelpers.load_data(CFG)
    aggr = orghelpers.get_incoming(db, CFG)
    tasks_open, tasks_all = orghelpers.get_totals_stat(db, CFG)

    orgreports.report_projects(aggr['projects'])

    output = orgreports.report_unfinished(aggr['unfinished'], CFG)
    if output and aggr['incoming']:
        print()
    orgreports.report_incoming(aggr['incoming'], CFG)

    print()
    test_report(aggr['incoming'], aggr['unfinished'], CFG)

    print("[%d/%d]" % (tasks_open, tasks_all))

if __name__ == "__main__":
    main()
