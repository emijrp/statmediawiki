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


#fix
#mirar como usa las fechas aquí http://matplotlib.sourceforge.net/examples/api/date_demo.html
#nube de puntos http://matplotlib.sourceforge.net/examples/api/unicode_minus.html
#dateranges http://matplotlib.sourceforge.net/examples/pylab_examples/date_demo_rrule.html

def revertsEvolution(cursor=None):
    """result = cursor.execute("SELECT rev_timestamp FROM revision WHERE 1 ORDER BY rev_timestamp ASC LIMIT 1")
    for row in result:
        return row[0], row[1]"""
    
    result = cursor.execute("SELECT rev_page, rev_id, rev_timestamp, rev_text_md5 FROM revision WHERE 1 ORDER BY rev_page, rev_timestamp ASC")
    page = []
    reverts = {}
    for row in result:
        rev_page = row[0]
        rev_id = row[1]
        rev_timestamp = row[2]
        rev_text_md5 = row[3]
        revision = [rev_page, rev_id, rev_timestamp, rev_text_md5]
        
        if page:
            if rev_page == page[0][0]: #new revision for this page
                page.append(revision)
            else: #previous page finished, analyse
                c = 0
                for temprev in page:
                    if temprev[3] in [temprev2[3] for temprev2 in page[:c]]: #is a revert of a previous rev in this page
                        temprevdate = datetime.date(year=int(temprev[2][0:4]), month=int(temprev[2][5:7]), day=int(temprev[2][8:10]))
                        if reverts.has_key(temprevdate):
                            reverts[temprevdate] += 1
                        else:
                            reverts[temprevdate] = 1
                    c += 1
                
                page = [revision] #reset
        else:
            page.append(revision)
    
    #fix, no analiza la última página, habría que repetir el código del for temprev in page, llevar mejor a una función core y llamar?
    
    reverts_list = [[x, y] for x, y in reverts.items()]
    reverts_list.sort()
    
    startdate = reverts_list[0][0]
    enddate = reverts_list[-1:][0][0]
    delta = datetime.timedelta(days=1)
    reverts_list = [] #reset, adding all days between startdate and enddate
    d = startdate
    while d < enddate:
        if reverts.has_key(d):
            reverts_list.append([d, reverts[d]])
        else:
            reverts_list.append([d, 0])
        d += delta


    from pylab import *
    from matplotlib.dates import DAILY, DateFormatter, rrulewrapper, RRuleLocator, drange

    rule = rrulewrapper(DAILY, byeaster=1, interval=1)
    loc = RRuleLocator(rule)
    formatter = DateFormatter('%Y-%m-%d')
    dates = drange(startdate, enddate, delta)

    ax = subplot(111)
    ax.set_ylabel('Reverts')
    ax.set_xlabel('Date (YYYY-MM-DD)')
    print '#'*100
    print len(dates)
    print dates
    print '#'*100
    print len(array([y for x, y in reverts_list]))
    print array([y for x, y in reverts_list])
    print '#'*100
    plot_date(dates, array([y for x, y in reverts_list]), 'o')
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(formatter)
    ax.set_title('Reverts evolution')
    ax.grid(True)
    labels = ax.get_xticklabels()
    setp(labels, rotation=30, fontsize=10)

    show()
