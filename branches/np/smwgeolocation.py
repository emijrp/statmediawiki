# -*- coding: utf-8  -*-

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
                    
                    cat = (start / catlimit) * catlimit
                    if geoipdb.has_key(cat):
                        geoipdb[cat].append([start, end, iso2])
                    else:
                        geoipdb[cat] = [ [start, end, iso2] ]
                c+=1
                if c % 10000 == 0:
                    print "Loaded %d ip ranges for geolocation" % (c)
    
    def getIPCountry(self, ip):
        global geoipdb
        
        t = ip.split(".")
        if len(t) == 4:
            ipnumber = int(t[3]) + int(t[2])*256 + int(t[1])*256*256 + int(t[0])*256*256*256
            cat = ipnumber - (ipnumber % catlimit)
            #print ipnumber, cat
            if geoipdb.has_key(cat):
                for start, end, iso2 in geoipdb[cat]:
                    if ipnumber>=start and ipnumber<=end:
                        return iso2
        return False

def GeoLocationGraph(cursor=None, range='', entity='', title='', subtitle='', color='', xlabel=''):
    if not cursor:
        print "ERROR, NO CURSOR"
        return
    
    t1=time.time()
    
    fig = pylab.figure()
    pylab.suptitle(title)
    
    subfig = fig.add_subplot(1,1,1)
    a = []
    if range == 'global':
        a = cursor.execute("select username from revision where ipedit=?", (1, ))
    elif range == 'page':
        a = cursor.execute("select username from revision where ipedit=? and title=?", (1, entity))
    
    x, y = [], []
    geo = GeoLocation()
    geo.load()
    countries = {}
    for row in a:
        country = geo.getIPCountry(row[0])
        if country: #puede ser FALSE si la base de datos no reconoce ese rango de ips
            if countries.has_key(country):
                countries[country] += 1
            else:
                countries[country] = 1
    
    countries_list = [[edits, country] for country, edits in countries.items()]
    countries_list.sort()
    countries_list.reverse()
    
    limit = 10
    x = [country for edits, country in countries_list[:limit]]
    y = [edits for edits, country in countries_list[:limit]]
    print countries_list[:limit], x, y
    
    rects = subfig.bar(numpy.arange(len(x)), y, align='center')
    subfig.legend()
    subfig.set_title(subtitle)
    subfig.set_xlabel('Country')
    subfig.set_xticks(numpy.arange(len(x)))
    subfig.set_xticklabels([str(i) for i in x])
    subfig.set_ylabel('Edits')
    
    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        subfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/50), str(height), ha='center', va='bottom')
    
    print title, 'generated in', time.time()-t1, 'secs'

