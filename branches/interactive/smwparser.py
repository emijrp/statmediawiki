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
    cursor.execute('''create table revision (rev_id integer, rev_title text, rev_page integer, rev_user_text text, rev_is_ipedit integer, rev_timestamp timestamp, rev_text_md5 text, rev_size integer, rev_comment text, rev_internal_links integer, rev_external_links integer, rev_interwikis integer, rev_sections integer)''')
    #rev_is_minor, rev_is_redirect, rev_highwords (bold/italics/bold+italics), rev_diff
    cursor.execute('''create table page (page_id integer, page_title text, page_editcount integer, page_creation_timestamp timestamp, page_last_timestamp timestamp, page_text text, page_internal_links integer, page_external_links integer, page_interwikis integer, page_sections integer)''') 
    #page_namespace, page_size (last rev size), page_views
    cursor.execute('''create table user (user_name text, user_is_ip integer, user_editcount integer)''') #fix, poner si es ip basándonos en ipedit?
    #user_id (viene en el dump? 0 para ips), user_is_anonymous (ips)
    conn.commit()

def generateUserTable(conn, cursor):
    result = cursor.execute("SELECT rev_user_text AS user_name, rev_is_ipedit AS user_is_ip, COUNT(*) AS user_editcount FROM revision WHERE 1 GROUP BY user_name")
    users = []
    for user_name, user_is_ip, user_editcount in result:
        users.append([user_name, user_is_ip, user_editcount])

    for user_name, user_is_ip, user_editcount in users:
        cursor.execute('INSERT INTO user VALUES (?,?,?)', (user_name, user_is_ip, user_editcount))
    conn.commit()

    print "GENERATED USER TABLE: %d" % (len(users))

def generateAuxTables(conn=None, cursor=None):
    print '#'*30, '\n', 'Generating auxiliar tables', '\n', '#'*30
    generateUserTable(conn=conn, cursor=cursor)

def parseMediaWikiXMLDump(dumpfilename, dbfilename):
    if dumpfilename.endswith('.7z'):
        s = subprocess.Popen('7z l %s' % dumpfilename, shell=True, stdout=subprocess.PIPE, bufsize=65535).stdout # fix, solo funciona en linux?
        sout = s.read()
        if not re.search(ur'(?im)Can not open file as archive', sout) and \
           not re.search(ur'(?im)1 files, 0 folders\n$', sout):
            print 'ERROR: the file %s contains more files than a .xml' % dumpfilename
            return 
            #os.rename(filename, '%s.corrupted' % filename)
    
    if os.path.exists(dbfilename): #si existe lo borramos, pues el usuario ha marcado sobreescribir, sino no entraría aquí #fix, mejor renombrar?
        os.remove(dbfilename)

    conn = sqlite3.connect(dbfilename)
    cursor = conn.cursor()

    # Create table
    createDB(conn=conn, cursor=cursor)

    limit = 1000
    c = 0
    c_page = 0
    t1 = time.time()
    tt = time.time()
    
    r_internal_links = re.compile(ur'(?im)(\[\[[^\|\]\r\n]+?(\|[^\|\]\r\n]*?)?\]\])')
    r_external_links = re.compile(ur'(?im)\b(ftps?|git|gopher|https?|irc|mms|news|svn|telnet|worldwind)://')
    # http://en.wikipedia.org/wiki/Special:SiteMatrix
    r_interwikis = re.compile(ur'(?im)(\[\[([a-z]{2,3}|simple|classical)(\-([a-z]{2,3}){1,2}|tara)?\:[^\[\]]+?\]\])')
    r_sections = re.compile(ur'(?im)^((?P<heading>={1,6})[^=]+\g<heading>[^=])')
    
    xml = xmlreader.XmlDump(dumpfilename, allrevisions=True)
    errors = 0
    errors_page = 0
    page_id = -1 #impossible value
    page_title = ''
    page_editcount = 0
    page_creation_timestamp = ''
    page_last_timestamp = ''
    page_text = ''
    page_internal_links = 0
    page_external_links = 0
    page_interwikis = 0
    page_sections = 0
    for x in xml.parse(): #parsing the whole dump
        # Create page entry if needed
        if page_id != -1 and page_id != x.id:
            if page_id and page_title and page_editcount and page_creation_timestamp and page_last_timestamp: #page_text not needed, it can be a blanked page
                #fix, si le llega una página duplicada, mete dos o sobreescribe?
                #fix add namespace detector
                #fix add rev_id actual para cada pagina
                #meter estos valores para cada página usando la última revisión del historial: rev_size, rev_internal_links, rev_external_links, rev_interwikis, rev_sections, rev_timestamp, rev_text_md5; NO: rev_comment
                cursor.execute('INSERT INTO page VALUES (?,?,?,?,?,?,?,?,?,?)', (page_id, page_title, page_editcount, page_creation_timestamp, page_last_timestamp, page_text, page_internal_links, page_external_links, page_interwikis, page_sections))
                #conn.commit()
                c_page += 1
            else:
                print '#'*30, '\n', 'ERROR PAGE:' , page_id, page_title, page_editcount, page_creation_timestamp, page_last_timestamp, 'text (', len(page_text), 'bytes)', page_text[:100], '\n', '#'*30
                errors_page += 1
            #reset values
            page_id = x.id
            page_title = x.title
            page_editcount = 0
            page_creation_timestamp = ''
            page_last_timestamp = ''
            page_text = ''
            page_internal_links = 0
            page_external_links = 0
            page_interwikis = 0
            page_sections = 0
        
        page_editcount += 1
        rev_id = int(x.revisionid)
        rev_title = x.title
        rev_page = x.id
        if page_id == -1:
            page_id = rev_page
        rev_user_text = x.username
        rev_is_ipedit = x.ipedit and 1 or 0 #fix, las ediciones de MediaWiki default cuentan como IP?
        rev_timestamp = datetime.datetime(year=int(x.timestamp[0:4]), month=int(x.timestamp[5:7]), day=int(x.timestamp[8:10]), hour=int(x.timestamp[11:13]), minute=int(x.timestamp[14:16]), second=int(x.timestamp[17:19]))
        x_text = x.text
        x_text_encoded = x.text.encode('utf-8')
        rev_text_md5 = hashlib.md5(x_text_encoded).hexdigest()
        rev_size = len(x_text_encoded)
        rev_comment = x.comment or ''
        rev_internal_links = len(re.findall(r_internal_links, x_text_encoded)) #fix enlaces internos (esto incluye los iws, descontarlos después?)
        rev_external_links = len(re.findall(r_external_links, x_text_encoded)) #external links http://en.wikipedia.org/wiki/User:Emijrp/External_Links_Ranking
        rev_interwikis = len(re.findall(r_interwikis, x_text_encoded))
        rev_internal_links -= rev_interwikis # removing interwikis from [[links]]
        rev_sections = len(re.findall(r_sections, x_text_encoded))
        
        #saving values if this revision is the first or the last of a page
        if not page_creation_timestamp or rev_timestamp < page_creation_timestamp:
            page_creation_timestamp = rev_timestamp
        if not page_last_timestamp or rev_timestamp > page_last_timestamp:
            page_last_timestamp = rev_timestamp
            page_text = x_text
            page_internal_links = rev_internal_links
            page_external_links = 0
            page_interwikis = 0
            page_sections = 0
        
        # create tuple
        t = (rev_id, rev_title, rev_page, rev_user_text, rev_is_ipedit, rev_timestamp, rev_text_md5, rev_size, rev_comment, rev_internal_links, rev_external_links, rev_interwikis, rev_sections)
        
        xmlbug = (rev_id, rev_title, rev_page, rev_user_text)
        if not None in xmlbug and not '' in xmlbug:
            cursor.execute('INSERT INTO revision VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', t)
            c += 1
        else:
            #print t
            errors += 1
        
        if (c+errors) % limit == 0:
            print 'Analysed %d revisions [%d revs/sec]' % (c+errors, limit/(time.time()-t1))
            conn.commit()
            t1 = time.time()
        
    conn.commit() #para cuando son menos de limit o el resto
    print 'Total revisions [%d], correctly inserted [%d], errors [%d]' % (c+errors, c, errors)
    print 'Total pages [%d], correctly inserted [%d], errors [%d]' % (c_page+errors_page, c_page, errors_page)
    print 'Total time [%d secs or %2f minutes or %2f hours]' % (time.time()-tt, (time.time()-tt)/60.0, (time.time()-tt)/3600.0)

    #tablas auxiliares
    tt = time.time()
    generateAuxTables(conn=conn, cursor=cursor)
    print time.time()-tt, 'seconds'
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    filename = sys.argv[1]
    path = ''
    parseMediaWikiXMLDump(path, filename)
