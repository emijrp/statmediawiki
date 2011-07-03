#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2011 StatMediaWiki
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from Tkinter import *

import datetime
import sqlite3
import tkMessageBox

#fix cuenta los anónimos también, evitar esto? ofrecer dos gráficas?

def newusersEvolution(cursor=None):
    result = cursor.execute("SELECT STRFTIME('%Y-%m-%d', rev_timestamp) AS date, rev_user_text FROM revision WHERE 1 ORDER BY date ASC")
    newusers = {}
    for row in result:
        if not newusers.has_key(row[1]):
            newusers[row[1]] = datetime.date(year=int(row[0][0:4]), month=int(row[0][5:7]), day=int(row[0][8:10]))
    
    newusers2 = {}
    for newuser, date in newusers.items():
        if newusers2.has_key(date):
            newusers2[date] += 1
        else:
            newusers2[date] = 1
    
    newusers_list = [[x, y] for x, y in newusers2.items()]
    newusers_list.sort()
    
    startdate = newusers_list[0][0]
    enddate = newusers_list[-1:][0][0]
    delta = datetime.timedelta(days=1)
    newusers_list = [] #reset, adding all days between startdate and enddate
    d = startdate
    while d < enddate:
        if newusers2.has_key(d):
            newusers_list.append([d, newusers2[d]])
        else:
            newusers_list.append([d, 0])
        d += delta
    
    from pylab import *
    from matplotlib.dates import DAILY, DateFormatter, rrulewrapper, RRuleLocator, drange

    rule = rrulewrapper(DAILY, byeaster=1, interval=1)
    loc = RRuleLocator(rule)
    formatter = DateFormatter('%Y-%m-%d')
    dates = drange(startdate, enddate, delta)

    ax = subplot(111)
    ax.set_ylabel('Newusers')
    ax.set_xlabel('Date (YYYY-MM-DD)')
    print '#'*100
    print len(dates)
    print dates
    print '#'*100
    print len(array([y for x, y in newusers_list]))
    print array([y for x, y in newusers_list])
    print '#'*100
    plot_date(dates, array([y for x, y in newusers_list]), 'o', color='green')
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    ax.set_title('Newusers evolution')
    ax.grid(True)
    ax.set_yscale('log')
    labels = ax.get_xticklabels()
    setp(labels, rotation=30, fontsize=10)

    show()
    
