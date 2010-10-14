#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010 StatMediaWiki
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

import calendar
import sqlite3
import time
import xmlreader
import sys
import numpy
import pylab
import thread

#cada script .py es un analisis (usuarios ordenados por ediciones por ejemplo) y permiten ser llamados desde otro modulo (mediante llamada a función) o desde consola y con salida por pantalla, csv, svg ,png eps si corresponde, etc

def activity(cursor=None, range='', entity='', title='', subtitle='', color='', xlabel='', timesplit=''):
    if not cursor:
        print "ERROR, NO CURSOR"
        return
    
    t1=time.time()
    
    fig = pylab.figure()
    pylab.suptitle(title)
    
    subfig = fig.add_subplot(1,1,1)
    result = []
    if range == 'global':
        result = cursor.execute("SELECT STRFTIME(?, rev_timestamp) AS timesplit, COUNT(*) AS count FROM revision WHERE 1 GROUP BY timesplit ORDER BY timesplit ASC", (timesplit, ))
    elif range == 'user':
        result = cursor.execute("SELECT STRFTIME(?, rev_timestamp) AS timesplit, COUNT(*) AS count FROM revision WHERE username=? GROUP BY timesplit ORDER BY timesplit ASC", (timesplit, entity))
    elif range == 'page':
        result = cursor.execute("SELECT STRFTIME(?, rev_timestamp) AS timesplit, COUNT(*) AS count FROM revision WHERE title=? GROUP BY timesplit ORDER BY timesplit ASC", (timesplit, entity))
    
    x, y = [], []
    for timesplit, count in result:
        print timesplit, count
        x.append(int(timesplit))
        y.append(int(count))
    
    rects = subfig.bar(numpy.arange(len(x)), y, color=color, align='center')
    subfig.legend()
    subfig.set_title(subtitle)
    subfig.set_xlabel(xlabel)
    subfig.set_xticks(numpy.arange(len(x)))
    subfig.set_xticklabels([str(i) for i in x])
    subfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        subfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/50), str(height), ha='center', va='bottom')
    
    print title, 'generated in', time.time()-t1, 'secs'

def activityyearly(cursor=None, range='', entity='', title=''):
    activity(cursor=cursor, range=range, entity=entity, title=title, subtitle='Activity by year', color='#88aa33', xlabel='Year', timesplit='%Y')

def activitymonthly(cursor=None, range='', entity='', title=''):
    activity(cursor=cursor, range=range, entity=entity, title=title, subtitle='Activity by month', color='#aa3388', xlabel='Month', timesplit='%m')

def activitydow(cursor=None, range='', entity='', title=''):
    activity(cursor=cursor, range=range, entity=entity, title=title, subtitle='Activity by day of week', color='#3388aa', xlabel='Day of week', timesplit='%w')

def activityhourly(cursor=None, range='', entity='', title=''):
    activity(cursor=cursor, range=range, entity=entity, title=title, subtitle='Activity by hour', color='#1177bb', xlabel='Hour', timesplit='%H')

def activityall(cursor=None, range='', entity='', title=''):
    #FIX: no funciona, solo se muestra la primera y las otras conforme se va cerrando ventanas, meter las 4 en una?
    activityyearly(cursor=cursor, range=range, entity=entity, title=title)
    activitymonthly(cursor=cursor, range=range, entity=entity, title=title)
    activitydow(cursor=cursor, range=range, entity=entity, title=title)
    activityhourly(cursor=cursor, range=range, entity=entity, title=title)
