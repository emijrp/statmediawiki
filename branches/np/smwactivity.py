# -*- coding: utf-8  -*-

import calendar
import sqlite3
import time
import xmlreader
import sys
import numpy as np
import pylab as p

#cada script .py es un analisis (usuarios ordenados por ediciones por ejemplo) y permiten ser llamados desde otro modulo (mediante llamada a función) o desde consola y con salida por pantalla, csv, svg ,png eps si corresponde, etc

def activity(cursor, title='', subtitle='', xlabel='', timesplit=''):
    t1=time.time()
    
    fig = p.figure()
    p.suptitle(title)
    
    subfig = fig.add_subplot(1,1,1)
    a = cursor.execute("select strftime('%%%s', timestamp) as time, count(*) as count from revision where 1 group by time order by time asc" % (timesplit))
    
    x, y = [], []
    for row in a:
        print row
        x.append(int(row[0]))
        y.append(int(row[1]))
    
    rects = subfig.bar(np.arange(len(x)), y, color='#88aa33', align='center')
    subfig.legend()
    subfig.set_title(subtitle)
    subfig.set_xlabel(xlabel)
    subfig.set_xticks(np.arange(len(x)))
    subfig.set_xticklabels([str(i) for i in x])
    subfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        subfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/50), str(height), ha='center', va='bottom')
    
    p.show()

def activityyearly(cursor, title=''):
    activity(cursor=cursor, title=title, subtitle='Activity by year', xlabel='Year', timesplit='Y')

def activitymonthly(cursor, title=''):
    activity(cursor=cursor, title=title, subtitle='Activity by month', xlabel='Month', timesplit='m')

def activitydow(cursor, title=''):
    activity(cursor=cursor, title=title, subtitle='Activity by day of week', xlabel='Day of week', timesplit='w')

def activityhourly(cursor, title=''):
    activity(cursor=cursor, title=title, subtitle='Activity by hour', xlabel='Hour', timesplit='H')

def activityall(cursor, title=''):
    #a = cursor.execute('select username, count(*) from revision group by username order by count(*) desc limit 30')
    #a = cursor.execute("select title, revisionid, timestamp from revision where timestamp<datetime('2004-06-12 10:00:00') limit 30")
    #a = cursor.execute("select title, revisionid, timestamp, datetime(strftime('%Y-%m-%dT%H:%M:%S', timestamp)) from revision where 1 limit 30")
    
    
    t1=time.time()
    
    fig = p.figure()
    p.suptitle(title)
    
    #year
    yearfig = fig.add_subplot(2,2,1)
    a = cursor.execute("select strftime('%Y', timestamp) as time, count(*) as count from revision where 1 group by time order by time asc")
    
    x, y = [], []
    for row in a:
        print row
        x.append(int(row[0]))
        y.append(int(row[1]))
    
    print x, y
    rects = yearfig.bar(np.arange(len(x)), y, color='#88aa33', align='center')
    #yearfig.plot(np.arange(len(x)), y, 'bo-')
    yearfig.legend()
    yearfig.set_title('Activity by year')
    yearfig.set_xlabel("Year")
    yearfig.set_xticks(np.arange(len(x)))
    yearfig.set_xticklabels([str(i) for i in x])
    yearfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        yearfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/25), str(height), ha='center', va='bottom')
    
    #month
    monthfig = fig.add_subplot(2,2,2)
    a = cursor.execute("select strftime('%m', timestamp) as time, count(*) as count from revision where 1 group by time order by time asc")
    
    x, y = [], []
    for row in a:
        print row
        x.append(int(row[0]))
        y.append(int(row[1]))
    
    rects = monthfig.bar(np.arange(len(x)), y, color='#aa3388', align='center')
    monthfig.legend()
    monthfig.set_title('Activity by month')
    monthfig.set_xlabel("Month")
    monthfig.set_xticks(np.arange(len(x)))
    monthname = lambda month_num:calendar.month_name[month_num]
    monthfig.set_xticklabels([monthname(i)[:3] for i in x])
    monthfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        monthfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/25), str(height), ha='center', va='bottom')
    
    #day
    dowfig = fig.add_subplot(2,2,3)
    a = cursor.execute("select strftime('%w', timestamp) as time, count(*) as count from revision where 1 group by time order by time asc")
    
    x, y = [], []
    for row in a:
        print row
        x.append(int(row[0]))
        y.append(int(row[1]))
    
    rects = dowfig.bar(np.arange(len(x)), y, color='#3388aa', align='center')
    dowfig.legend()
    dowfig.set_title('Activity by day of week')
    dowfig.set_xlabel('Day of week')
    dowfig.set_xticks(np.arange(len(x)))
    dowfig.set_xticklabels([str(i) for i in x])
    dowfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        dowfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/25), str(height), ha='center', va='bottom')
    
    #hour
    hourfig = fig.add_subplot(2,2,4)
    a = cursor.execute("select strftime('%H', timestamp) as time, count(*) as count from revision where 1 group by time order by time asc")
    
    x, y = [], []
    for row in a:
        print row
        x.append(int(row[0]))
        y.append(int(row[1]))
    
    rects = hourfig.bar(np.arange(len(x)), y, color='#88aa00', align='center')
    hourfig.legend()
    hourfig.set_title('Activity by hour')
    hourfig.set_xlabel('Hour')
    hourfig.set_xticks(np.arange(len(x)))
    hourfig.set_xticklabels([str(i) for i in x])
    hourfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        hourfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/25), str(height), ha='center', va='bottom')
    
    print 'Generated in', time.time()-t1, 'secs'
    
    p.show()
    
    
    


