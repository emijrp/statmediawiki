# -*- coding: utf-8  -*-

import re
import urllib
import os
import tkMessageBox

import smwparser

def download(father, family, lang):
    #añadir posibilidad de descargar otros a parte del last
    #verificar md5
    names = {'wikipedia': 'wiki', 'wiktionary': 'wikt'}
    
    dumpsdir = 'dumps'
    if not os.path.exists(dumpsdir):
        os.makedirs(dumpsdir)
    
    filename = ''
    url = ''
    if father == 'wikimedia':
        filename = '%s%s-latest-pages-meta-history.xml.7z' % (lang, names[family])
        url = 'http://download.wikimedia.org/%s%s/latest/%s' % (lang, names[family], filename)
    elif father == 'wikia':
        filename = '%s-pages_full.xml.gz' % (lang)
        url = '' # la capturamos de Special:Statistics ya que a veces cambia (ver recipes.wikia.com)
        f = urllib.urlopen('http://%s.wikia.com/wiki/Special:Statistics' % lang)
        raw = f.read()
        f.close()
        m = re.findall(ur'(http://wiki-stats.wikia.com/./../[^\/]+?/pages_full.xml.gz)', raw) 
        if m:
            url = m[0]
        else:
            print "ERROR WHILE RETRIEVING DUMP FROM WIKIA"
        
    os.system('wget %s -O %s/%s -c' % (url, dumpsdir, filename))
    
    #chequear md5
    
    print 'OK!'
    tkMessageBox.showinfo("OK", "Download complete")
    smwparser.parseWikimediaXML(path=dumpsdir, filename=filename)
    

