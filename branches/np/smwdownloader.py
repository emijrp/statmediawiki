# -*- coding: utf-8  -*-

import re
import urllib
import os
import tkMessageBox

import smwparser

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
    os.system('wget %s -O %s/%s -c' % (url, dumpsdir, filename))
    
    #chequear md5
    
    print 'Download OK!'
    tkMessageBox.showinfo("OK", "Download complete")
    smwparser.parseMediaWikiXMLDump(path=dumpsdir, filename=filename)

def downloadWikiaDump(wiki):
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
    print 'Download OK!'
    tkMessageBox.showinfo("OK", "Download complete")
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
