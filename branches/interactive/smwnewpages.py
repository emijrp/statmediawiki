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

def newpagesEvolution(cursor=None, title=''):
    result = cursor.execute("SELECT STRFTIME('%Y-%m-%d', page_creation_timestamp) AS date, COUNT(*) AS count FROM page WHERE 1 GROUP BY date ORDER BY date ASC")
    newpages = {}
    for row in result:
        d = datetime.date(year=int(row[0][0:4]), month=int(row[0][5:7]), day=int(row[0][8:10]))
        newpages[d] = row[1]
    
    newpages_list = [[x, y] for x, y in newpages.items()]
    newpages_list.sort()
    
    startdate = newpages_list[0][0]
    enddate = newpages_list[-1:][0][0]
    delta = datetime.timedelta(days=1)
    newpages_list = [] #reset, adding all days between startdate and enddate
    d = startdate
    while d < enddate:
        if newpages.has_key(d):
            newpages_list.append([d, newpages[d]])
        else:
            newpages_list.append([d, 0])
        d += delta
    
    import pylab
    from matplotlib.dates import DateFormatter, rrulewrapper, RRuleLocator, drange

    loc = pylab.MonthLocator(bymonth=(1,6))
    formatter = DateFormatter('%Y-%m-%d')
    dates = drange(startdate, enddate, delta)

    fig = pylab.figure()
    ax = fig.add_subplot(1,1,1)
    ax.set_ylabel('Newpages')
    ax.set_xlabel('Date (YYYY-MM-DD)')
    print '#'*100
    print len(dates)
    print dates
    print '#'*100
    print len(pylab.array([y for x, y in newpages_list]))
    print pylab.array([y for x, y in newpages_list])
    print '#'*100
    pylab.plot_date(dates, pylab.array([y for x, y in newpages_list]), 'o')
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    ax.set_title(title)
    ax.grid(True)
    ax.set_yscale('log')
    labels = ax.get_xticklabels()
    pylab.setp(labels, rotation=30, fontsize=10)
