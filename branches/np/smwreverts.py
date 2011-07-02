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

#import numpy as np
import matplotlib
import matplotlib.pyplot as plt

#fix
#mirar como usa las fechas aquí http://matplotlib.sourceforge.net/examples/api/date_demo.html
#nube de puntos http://matplotlib.sourceforge.net/examples/api/unicode_minus.html

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
                        temprevdate = temprev[2][:10]
                        if reverts.has_key(temprevdate):
                            reverts[temprevdate] += 1
                        else:
                            reverts[temprevdate] = 1
                    c += 1
                
                page = [revision] #reset
        else:
            page.append(revision)
        
    reverts_list = [[revertday, revertsnum] for revertday, revertsnum in reverts.items()]
    reverts_list.sort()
    
    startdate = datetime.datetime(year=int(reverts_list[0][0][:4]), month=int(reverts_list[0][0][5:7]), day=int(reverts_list[0][0][8:10]))
    enddate = datetime.datetime(year=int(reverts_list[-1:][0][0][:4]), month=int(reverts_list[-1:][0][0][5:7]), day=int(reverts_list[-1:][0][0][8:10]))
    
    while startdate != enddate:
        tempdate = startdate.strftime('%Y-%m-%d')
        print startdate, reverts.has_key(tempdate) and reverts[tempdate] or 0
        startdate += datetime.timedelta(days=1)

    matplotlib.rcParams['axes.unicode_minus'] = False
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(range(len(reverts_list)), [y for x, y in reverts_list], '.')
    ax.set_title('Reverts evolution')
    plt.show()
