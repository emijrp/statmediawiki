# -*- coding: utf-8  -*-

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
    filename = '%s%s-latest-pages-meta-history.xml.7z' % (lang, names[family])
    os.system('wget http://download.wikimedia.org/%s%s/latest/%s -O %s/%s -c' % (lang, names[family], filename, dumpsdir, filename))
    
    #chequear md5
    
    print 'OK!'
    tkMessageBox.showinfo("OK", "Download complete")
    smwparser.parseWikimediaXML(path=dumpsdir, filename=filename)
    

