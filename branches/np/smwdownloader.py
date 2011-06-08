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

import re
import sys
import subprocess
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

def downloadWikimediaDump(wiki, filename):
    #añadir posibilidad de descargar otros a parte del last
    #verificar md5
    z7filename = '%s-latest-pages-meta-history.xml.7z' % (wiki)
    url = 'http://download.wikimedia.org/%s/latest/%s' % (wiki, z7filename)
    f = urllib.urlretrieve(url, filename, reporthook=downloadProgress)

    #fix chequear md5

def downloadWikiaDump(wiki, filename):
    url = '' # la capturamos de Special:Statistics ya que a veces cambia (ver recipes.wikia.com)
    f = urllib.urlopen('http://%s.wikia.com/wiki/Special:Statistics' % (wiki))
    raw = f.read()
    f.close()
    m = re.findall(ur'(http://[^/]+.wikia.com/./../[^\/]+?/pages_full.xml.gz)', raw)
    if m:
        url = m[0]
    if url:
        f = urllib.urlretrieve(url, filename, reporthook=downloadProgress)
    else:
        print "ERROR WHILE RETRIEVING DUMP FROM WIKIA"

def downloadWikiTeamDump(wiki, filename):
    #verificar md5
    z7filename = '%s-history.xml.7z' % (wiki)
    url = 'http://wikiteam.googlecode.com/files/%s' % (z7filename)
    f = urllib.urlretrieve(url, filename, reporthook=downloadProgress)

    #fix chequear md5
    
    #remove other than .xml files inside 7z
    print 'Removing not needed files inside the 7z'
    os.system("7z d %s *.txt *.html" % (filename))
    s = subprocess.Popen('7z l %s' % filename, shell=True, stdout=subprocess.PIPE, bufsize=65535).stdout
    if not re.search(ur'(?m)1 files, 0 folders\n$', s.read()):
        print 'ERROR: the file contains more files than a .xml, renaming to .corrupted'
        os.rename(filename, '%s.corrupted' % filename)

def downloadCitizendiumDump(wiki, filename):
    #añadir posibilidad de descargar otros a parte del last
    #verificar md5
    url = 'http://locke.citizendium.org/download/%s.dump.current.xml.gz' % (wiki)
    f = urllib.urlretrieve(url, filename, reporthook=downloadProgress)

    #fix chequear md5

def downloadWikimediaList():
    projects = []

    f = urllib.urlopen('http://download.wikimedia.org/backup-index.html')
    raw = f.read()
    f.close()

    m = re.compile(ur'<a href="(?P<wikiname>[^\/]+?)/\d{8}">').finditer(raw)
    [projects.append(i.group('wikiname')) for i in m]

    projects.sort()

    return projects

def downloadWikiaList():
    projects = ['answers', 'dc', 'efemerides', 'eq2', 'inciclopedia', 'familypedia', 'icehockey', 'lyrics', 'marveldatabase', 'memory-beta', 'memoryalpha', 'psychology', 'recipes', 'swfanon', 'starwars', 'uncyclopedia', 'vintagepatterns', 'wow']
    projects.sort()

    return projects

def downloadWikiTeamList():
    projects = []
    
    f = urllib.urlopen('http://code.google.com/p/wikiteam/downloads/list')
    raw = f.read()
    f.close()
    
    m = re.compile(ur'<a href="http://wikiteam\.googlecode\.com/files/(?P<wikiname>[^=]+\-\d+)\-history\.xml\.7z" onclick=').finditer(raw)
    [projects.append(i.group('wikiname')) for i in m]
    projects.sort()
    
    return projects
