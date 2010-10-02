# -*- coding: utf-8  -*-

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
    a = []
    if range == 'global':
        a = cursor.execute("select strftime(?, timestamp) as time, count(*) as count from revision where 1 group by time order by time asc", (timesplit, ))
    elif range == 'user':
        a = cursor.execute("select strftime(?, timestamp) as time, count(*) as count from revision where username=? group by time order by time asc", (timesplit, entity))
    elif range == 'page':
        a = cursor.execute("select strftime(?, timestamp) as time, count(*) as count from revision where title=? group by time order by time asc", (timesplit, entity))
    
    x, y = [], []
    for row in a:
        print row
        x.append(int(row[0]))
        y.append(int(row[1]))
    
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
    #a = cursor.execute('select username, count(*) from revision group by username order by count(*) desc limit 30')
    #a = cursor.execute("select title, revisionid, timestamp from revision where timestamp<datetime('2004-06-12 10:00:00') limit 30")
    #a = cursor.execute("select title, revisionid, timestamp, datetime(strftime('%Y-%m-%dT%H:%M:%S', timestamp)) from revision where 1 limit 30")
    
    #FIX: no funciona, solo se muestra la primera y las otras conforme se va cerrando ventanas, meter las 4 en una?
    activityyearly(cursor=cursor, range=range, entity=entity, title=title)
    activitymonthly(cursor=cursor, range=range, entity=entity, title=title)
    activitydow(cursor=cursor, range=range, entity=entity, title=title)
    activityhourly(cursor=cursor, range=range, entity=entity, title=title)

