#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate examplare report out of org-mode.
(C) Tomasz bla Fortuna
"""

import orghelpers
import orgreports
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
    'resilient': True,
}

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

    print("[%d/%d]" % (tasks_open, tasks_all))

if __name__ == "__main__":
    main()
