# -*- coding: utf-8  -*-

import re
import sys
import urllib
import os
import tkMessageBox
import random

import smwparser

def downloadProgress(block_count, block_size, total_size):
    total_mb = total_size/1024/1024.0
    downloaded = block_count *(block_size/1024/1024.0)
    percent = downloaded/(total_mb/100.0)
    if not random.randint(0,10):
        print "%.1f MB of %.1f MB downloaded (%.2f%%)" %(downloaded, total_mb, percent)
    #sys.stdout.write("%.1f MB of %.1f MB downloaded (%.2f%%)" %(downloaded, total_mb, percent))
    #sys.stdout.flush()

def downloadWikimediaDump(wiki):
    #añadir posibilidad de descargar otros a parte del last
    #verificar md5
    dumpsdir = 'dumps'
    if not os.path.exists(dumpsdir):
        os.makedirs(dumpsdir)
    
    filename = ''
    url = ''
    filename = '%s-latest-pages-meta-history.xml.7z' % (wiki)
    url = 'http://download.wikimedia.org/%s/latest/%s' % (wiki, filename)
    pathfilename = '%s/%s' % (dumpsdir, filename)
    if not os.path.exists(pathfilename):
        f = urllib.urlretrieve(url, pathfilename, reporthook=downloadProgress)
    
    #fix chequear md5
    
    print 'Download OK!'
    smwparser.parseMediaWikiXMLDump(path=dumpsdir, filename=filename)

def downloadWikiaDump(wiki):
    dumpsdir = 'dumps'
    if not os.path.exists(dumpsdir):
        os.makedirs(dumpsdir)
    
    filename = '%s-pages_full.xml.gz' % (wiki)
    url = '' # la capturamos de Special:Statistics ya que a veces cambia (ver recipes.wikia.com)
    f = urllib.urlopen('http://%s.wikia.com/wiki/Special:Statistics' % (wiki))
    raw = f.read()
    f.close()
    m = re.findall(ur'(http://wiki-stats.wikia.com/./../[^\/]+?/pages_full.xml.gz)', raw) 
    if m:
        url = m[0]
    else:
        print "ERROR WHILE RETRIEVING DUMP FROM WIKIA"
    pathfilename = '%s/%s' % (dumpsdir, filename)
    if not os.path.exists(pathfilename):
        f = urllib.urlretrieve(url, pathfilename, reporthook=downloadProgress)
    print 'Download OK!'
    smwparser.parseMediaWikiXMLDump(path=dumpsdir, filename=filename)
    
def downloadWikimediaList():
    projects = []
    
    f = urllib.urlopen('http://download.wikimedia.org/backup-index.html')
    raw = f.read()
    f.close()
    
    m = re.findall(ur'<a href="([^\/]+?)/\d{8}">', raw)
    if m:
        [projects.append(i) for i in m]
    
    projects.sort()
    
    return projects
