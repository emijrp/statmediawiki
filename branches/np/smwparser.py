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

import datetime
import re
import sqlite3
import subprocess
import time
import xmlreader
import sys
import os
import hashlib
import tkMessageBox

#TODO:
#campos adicionales: número de enlaces, categorías, ficheros, plantillas, etc
#capturar los namespaces del comienzo del XML y meter un campo namespace en la tabla page

#fix filtrar Mediawiki default (que aparece como ip)
#todo añadir un campo a la base de datos como último apso, para indicar que todo el parseo fue bien (esto sirve para avisar al usuario cuando hace #Load que el fichero está "corrupto" y debe reparsear)

"""

regexps para el parser
#imágenes y ficheros
#categorías
#iws
re.compile(ur"#\s*(REDIRECT|local name)\s*\[\[[^\|\]]+?(\|[^\|\]]*?)?\]\]")

"""

def createDB(conn=None, cursor=None):
    #en comentarios cosas que se pueden añadir
    #algunas ideas de http://git.libresoft.es/WikixRay/tree/WikiXRay/parsers/dump_sax_research.py
    cursor.execute('''create table image (img_name text)''') #quien la ha subido? eso no está en el xml, sino en pagelogging...
    cursor.execute('''create table revision (rev_id integer, rev_title text, rev_page integer, rev_user_text text, rev_is_ipedit integer, rev_timestamp timestamp, rev_text_md5 text, rev_size integer, rev_comment text, rev_links integer, rev_external_links integer, rev_interwikis integer, rev_sections integer)''')
    #rev_is_minor, rev_is_redirect, rev_highwords (bold/italics/bold+italics)
    cursor.execute('''create table page (page_id integer, page_title text, page_editcount integer, page_creation_timestamp timestamp)''') 
    #page_namespace, page_size (last rev size), page_views
    cursor.execute('''create table user (user_name text, user_editcount integer)''') #fix, poner si es ip basándonos en ipedit?
    #user_id (viene en el dump? 0 para ips), user_is_anonymous (ips)
    conn.commit()

def generatePageTable(conn, cursor):
    page_creation_timestamps = {}
    result = cursor.execute("SELECT rev_page, rev_id, rev_timestamp FROM revision WHERE 1 ORDER BY rev_page ASC, rev_timestamp ASC")
    page = ''
    timestamps = []
    for rev_page, rev_id, rev_timestamp in result:
        if page:
            if page != rev_page:
                timestamps.sort() # ya debería estar ordenado
                page_creation_timestamps[page] = timestamps[0]
                page = rev_page
                timestamps = [rev_timestamp]
            else:
                timestamps.append(rev_timestamp)
        else:
            page = rev_page
            timestamps = [rev_timestamp]
    timestamps.sort() # ya debería estar ordenado
    page_creation_timestamps[page] = timestamps[0]
    
    result = cursor.execute("SELECT rev_page AS page_id, rev_title AS page_title, COUNT(*) AS page_editcount FROM revision WHERE 1 GROUP BY page_id")
    pages = []
    for page_id, page_title, page_editcount in result:
        pages.append([page_id, page_title, page_editcount, page_creation_timestamps[page_id]])

    for page_id, page_title, page_editcount, page_creation_timestamp in pages:
        cursor.execute('INSERT INTO page VALUES (?,?,?,?)', (page_id, page_title, page_editcount, page_creation_timestamp))
    conn.commit()

    print "GENERATED PAGE TABLE: %d" % (len(pages))

def generateUserTable(conn, cursor):
    result = cursor.execute("SELECT rev_user_text AS user_name, COUNT(*) AS user_editcount FROM revision WHERE 1 GROUP BY user_name")
    c=0
    users = []
    for user_name, user_editcount in result:
        c+=1
        users.append([user_name, user_editcount])

    for user_name, user_editcount in users:
        cursor.execute('INSERT INTO user VALUES (?,?)', (user_name, user_editcount))
    conn.commit()

    print "GENERATED USER TABLE: %d" % (c)

def generateAuxTables(conn=None, cursor=None):
    generatePageTable(conn=conn, cursor=cursor)
    generateUserTable(conn=conn, cursor=cursor)

def parseMediaWikiXMLDump(dumpfilename, dbfilename):
    if dumpfilename.endswith('.7z'):
        s = subprocess.Popen('7z l %s' % dumpfilename, shell=True, stdout=subprocess.PIPE, bufsize=65535).stdout
        sout = s.read()
        if not re.search(ur'(?im)Can not open file as archive', sout) and \
           not re.search(ur'(?im)1 files, 0 folders\n$', sout):
            print 'ERROR: the file %s contains more files than a .xml' % dumpfilename
            return 
            #os.rename(filename, '%s.corrupted' % filename)
    
    if os.path.exists(dbfilename): #si existe lo borramos, pues el usuario ha marcado sobreescribir, sino no entraría aquí
        os.remove(dbfilename)

    conn = sqlite3.connect(dbfilename)
    cursor = conn.cursor()

    # Create table
    createDB(conn=conn, cursor=cursor)

    limit = 10000
    c = 0
    i=0
    t1=time.time()
    tt=time.time()
    
    r_links = re.compile(ur'(?im)(\[\[[^\|\]]+?(\|[^\]\|]*?)?\]\])')
    r_external_links = re.compile(ur'(?im)\b(ftps?|git|gopher|https?|irc|mms|news|svn|telnet|worldwind)://')
    # http://en.wikipedia.org/wiki/Special:SiteMatrix
    r_interwikis = re.compile(ur'(?im)(\[\[([a-z]{2,3}|simple|classical)(\-([a-z]{2,3}){1,2}|tara)?\:[^\[\]]+?\]\])')
    r_sections = re.compile(ur'(?im)^((={1,6})[^=]+\2[^=])')
    
    xml = xmlreader.XmlDump(dumpfilename, allrevisions=True)
    errors = 0
    for x in xml.parse(): #parsing the whole dump
        rev_id = int(x.revisionid)
        rev_title = x.title
        rev_page = x.id
        rev_user_text = x.username
        rev_is_ipedit = x.ipedit and 1 or 0 #fix, las ediciones de MediaWiki default cuentan como IP?
        rev_timestamp = datetime.datetime(year=int(x.timestamp[0:4]), month=int(x.timestamp[5:7]), day=int(x.timestamp[8:10]), hour=int(x.timestamp[11:13]), minute=int(x.timestamp[14:16]), second=int(x.timestamp[17:19]))
        x_text_encoded = x.text.encode('utf-8')
        rev_text_md5 = hashlib.md5(x_text_encoded).hexdigest()
        rev_size = len(x_text_encoded)
        rev_comment = x.comment or ''
        rev_links = len(re.findall(r_links, x_text_encoded)) #fix enlaces internos (esto incluye los iws, descontarlos después?)
        rev_external_links = len(re.findall(r_external_links, x_text_encoded)) #external links http://en.wikipedia.org/wiki/User:Emijrp/External_Links_Ranking
        rev_interwikis = len(re.findall(r_interwikis, x_text_encoded))
        rev_links -= rev_interwikis # removing interwikis from [[links]]
        rev_sections = len(re.findall(r_sections, x_text_encoded))
        
        t = (rev_id, rev_title, rev_page, rev_user_text, rev_is_ipedit, rev_timestamp, rev_text_md5, rev_size, rev_comment, rev_links, rev_external_links, rev_interwikis, rev_sections)
        
        xmlbug = (rev_id, rev_title, rev_page, rev_user_text)
        if not None in xmlbug and not '' in xmlbug:
            cursor.execute('INSERT INTO revision VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', t)
            i+=1
        else:
            #print t
            errors += 1

        c += 1
        if c % limit == 0:
            print 'Analysed %d [%d edits/sec]' % (c, limit/(time.time()-t1))
            conn.commit()
            t1=time.time()
    conn.commit() #para cuando son menos de limit o el resto
    print 'Total revisions [%d], correctly inserted [%d], errors [%d], time [%d secs, %2f minutes]' % (c, i, errors, time.time()-tt, (time.time()-tt)/60.0)

    #tablas auxiliares
    generateAuxTables(conn=conn, cursor=cursor)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    filename = sys.argv[1]
    path = ''
    parseMediaWikiXMLDump(path, filename)
