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

import csv
import gzip
import os
import sqlite3
import time
import urllib

import numpy
import pylab

class GeoLocation():
    global geoipdb
    global catlimit
    
    geoipdb = {}
    catlimit = 10000000 # split to make it faster
    
    def __init__(self):
        pass
    
    def load(self):
        # For details, see database scheme here http://software77.net/geo-ip/?license
        global geoipdb
        
        if not geoipdb:
            filename = "geoip/IpToCountry.csv.gz"
            if not os.path.exists(filename):
                print "Downloading GeoIP database from software77.net"
                urllib.urlretrieve("http://software77.net/geo-ip/?DL=1", filename)
            
            f = csv.reader(gzip.GzipFile(filename, "r"), delimiter=',', quotechar='"')
            c=0
            for row in f:
                # IP FROM,IP TO,REGISTRY,ASSIGNED,CTRY,CNTRY,COUNTRY
                if c!=0 and len(row) == 7 and not row[0].startswith('#'):
                    start = int(row[0])
                    end = int(row[1])
                    iso2 = row[4]
                    country = row[6]
                    
                    cat = (start / catlimit) * catlimit
                    if geoipdb.has_key(cat):
                        geoipdb[cat].append([start, end, iso2, country])
                    else:
                        geoipdb[cat] = [ [start, end, iso2, country] ]
                c+=1
                if c % 10000 == 0:
                    print "Loaded %d ip ranges for geolocation" % (c)
    
    def getIPCountry(self, ip):
        global geoipdb
        
        t = ip.split(".")
        if len(t) == 4:
            try:
                ipnumber = int(t[3]) + int(t[2])*256 + int(t[1])*256*256 + int(t[0])*256*256*256
                cat = ipnumber - (ipnumber % catlimit)
                #print ipnumber, cat
                if geoipdb.has_key(cat):
                    for start, end, iso2, country in geoipdb[cat]:
                        if ipnumber>=start and ipnumber<=end:
                            return country
            except:
                print "ERROR GEOIP", ip
        return False

def GeoLocationGraph(cursor=None, range='', entity='', title='', subtitle='', color='#44bb66', xlabel=''):
    if not cursor:
        print "ERROR, NO CURSOR"
        return
    
    t1=time.time()
    
    fig = pylab.figure()
    pylab.suptitle(title)
    
    subfig = fig.add_subplot(2,1,1)
    result = []
    if range == 'global':
        result = cursor.execute("SELECT rev_user_text FROM revision WHERE rev_is_ipedit=?", (1, ))
    elif range == 'page':
        result = cursor.execute("SELECT rev_user_text FROM revision WHERE rev_is_ipedit=? AND rev_page_title=?", (1, entity))
    
    x, y = [], []
    geo = GeoLocation()
    geo.load()
    countries = {}
    for row in result:
        country = geo.getIPCountry(row[0])
        if country: #puede ser FALSE si la base de datos no reconoce ese rango de ips
            if countries.has_key(country):
                countries[country] += 1
            else:
                countries[country] = 1
    
    countries_list = [[edits, country] for country, edits in countries.items()]
    countries_list.sort()
    countries_list.reverse()
    
    limit = 9
    x = [country for edits, country in countries_list]
    y = [edits for edits, country in countries_list]
    xlim = x[:limit]+['Other']
    ylim = y[:limit]+[sum(y[limit:])]
    print countries_list[:limit], xlim, ylim
    
    rects = subfig.bar(numpy.arange(len(xlim)), ylim, color=color, align='center')
    subfig.legend()
    subfig.set_title(subtitle)
    subfig.set_xlabel('Country')
    subfig.set_xticks(numpy.arange(len(xlim)))
    subfig.set_xticklabels([str(i) for i in xlim])
    subfig.set_ylabel('Geolocated edits by unregistered users')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        subfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/50), str(height), ha='center', va='bottom')
    
    #pie chart
    import smwsummary
    subfig2 = fig.add_subplot(2,1,2)
    labels = ['Registered user edits', 'Anonymous user edits']
    fracs = [smwsummary.editsByRegisteredUsers(cursor=cursor), smwsummary.editsByAnonymousUsers(cursor=cursor)]
    explode = (0, 0.15) # anons out
    pylab.pie(fracs, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)
    pylab.title('Edits by user class')
    
    print title, 'generated in', time.time()-t1, 'secs'

