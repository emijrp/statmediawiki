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

#TODO: unificar las funciones parsemywiki y parsemediawiki en la medida de lo posible, ahora mismo hay mucho código repetido
#campos adicionales: número de enlaces, categorías, ficheros, plantillas, etc
#capturar los namespaces del comienzo del XML y meter un campo namespace en la tabla page

#fix filtrar Mediawiki default (que aparece como ip)
#todo añadir un campo a la base de datos como último apso, para indicar que todo el parseo fue bien (esto sirve para avisar al usuario cuando hace #Load que el fichero está "corrupto" y debe reparsear)

"""

regexps para el parser
re.compile(ur"\b\[\[[^\|\]]+?(\|[^\]\|]*?)?\]\]\b") # enlaces (esto incluye los iws, descontarlos después?)
re.compile(ur"\b(http|ftp)s?://") #externos
#imágenes y ficheros
#categorías
#iws
re.compile(ur"#\s*(REDIRECT|locale)\s*\[\[[^\|\]]+?(\|[^\|\]]*?)?\]\]")

"""

def createDB(conn=None, cursor=None):
    cursor.execute('''create table image (img_name text)''')
    cursor.execute('''create table revision (rev_id integer, rev_title text, rev_page_id integer, rev_username text, rev_is_ipedit integer, rev_timestamp timestamp, rev_md5 text)''')
    cursor.execute('''create table page (page_id integer, page_title text, page_editcount integer)''') #fix, poner si es ip basándonos en ipedit?
    cursor.execute('''create table user (user_name text, user_editcount integer)''')
    conn.commit()

def generatePageTable(conn, cursor):
    result = cursor.execute("SELECT rev_page_id AS page_id, rev_title AS page_title, COUNT(*) AS page_editcount FROM revision WHERE 1 GROUP BY page_id")
    c = 0
    pages = []
    for page_id, page_title, page_editcount in result:
        c += 1
        pages.append([page_id, page_title, page_editcount])

    for page_id, page_title, page_editcount in pages:
        cursor.execute('INSERT INTO page VALUES (?,?,?)', (page_id, page_title, page_editcount))
    conn.commit()

    print "GENERATED PAGE TABLE: %d" % (c)

def generateUserTable(conn, cursor):
    result = cursor.execute("SELECT rev_username AS user_name, COUNT(*) AS user_editcount FROM revision WHERE 1 GROUP BY user_name")
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
    xml = xmlreader.XmlDump(dumpfilename, allrevisions=True)
    for x in xml.parse():
        timestamp = datetime.datetime(year=int(x.timestamp[0:4]), month=int(x.timestamp[5:7]), day=int(x.timestamp[8:10]), hour=int(x.timestamp[11:13]), minute=int(x.timestamp[14:16]), second=int(x.timestamp[17:19]))
        md5 = hashlib.md5(x.text.encode('utf-8')).hexdigest()
        ipedit = 0
        if x.ipedit: #fix, las ediciones de MediaWiki default cuentan como IP?
            ipedit = 1
        t = (x.revisionid, x.title, x.id, x.username, ipedit, timestamp, md5)

        if not None in t and not '' in t:
            cursor.execute('INSERT INTO revision VALUES (?,?,?,?,?,?,?)', t)
            i+=1
        else:
            print t

        c += 1
        if c % limit == 0:
            print limit/(time.time()-t1), 'ed/s'
            conn.commit()
            t1=time.time()
    conn.commit() #para cuando son menos de limit o el resto
    print 'Total revisions', c, 'Inserted', i, 'Total time', time.time()-tt, 'seg', (time.time()-tt)/60.0, 'min'

    #tablas auxiliares
    generateAuxTables(conn=conn, cursor=cursor)
    # We can also close the cursor if we are done with it
    cursor.close()
    conn.close()

def parseMediaWikiMySQLConnect(mywikicursor, path, filename):
    import MySQLdb
    print "FUSIONAR PARA EVITAR COMETER ERRORES EN LAS TABLAS"
    return

    if not os.path.exists(path):
        os.makedirs(path)
    filenamedb = '%s/%s' % (path, filename)

    if os.path.exists(filenamedb):
        print 'Ya existe un preprocesado para este proyecto'

        if tkMessageBox.askyesno("File exists", "A parsed file exists. Delete and re-parse?"):
            os.remove(filenamedb)
        else:
            return

    conn = sqlite3.connect(filenamedb)
    cursor = conn.cursor()

    # Create table
    createDB(cursor)

    limit = 10000
    c = 0
    i=0
    t1=time.time()
    tt=time.time()

    cursor.execute('SELECT rev_id, page_title, rev_page, rev_user_text, rev_timestamp FROM revision, page WHERE page_id=rev_page')
    result = cursor.fetchall() #TODO fix hacerlo sin el fetchall, por si el wiki es grande
    for page_title, rev_page, rev_user_text, rev_timestamp, rev_id in result:
        timestamp = datetime.datetime(year=int(rev_timestamp[0:4]), month=int(rev_timestamp[5:7]), day=int(rev_timestamp[8:10]), hour=int(rev_timestamp[11:13]), minute=int(rev_timestamp[14:16]), second=int(rev_timestamp[17:19]))
        md5 = 0#md5 = hashlib.md5(x.text.encode('utf-8')).hexdigest() #el texto esta en old_text de la tabla text
        ipedit = False#is ip?
        t = (rev_id, page_title, rev_page, rev_user_text, ipedit, timestamp, md5)

        if not None in t and not '' in t:
            cursor.execute('INSERT INTO revision VALUES (?,?,?,?,?,?,?)', t)
            i+=1
        else:
            print t

        c += 1
        if c % limit == 0:
            print limit/(time.time()-t1), 'ed/s'
            conn.commit()
            t1=time.time()
    conn.commit() #para cuando son menos de limit o el resto
    print 'Total revisions', c, 'Inserted', i, 'Total time', time.time()-tt, 'seg', (time.time()-tt)/60.0, 'min'

    #tablas auxiliares
    generateAuxTables(conn=conn, cursor=cursor)

    # We can also close the cursor if we are done with it
    cursor.close()
    conn.close()

    print 'OK!'
    tkMessageBox.showinfo("OK", "Parsing complete")

if __name__ == "__main__":
    filename = sys.argv[1]
    path = ''
    parseWikimediaXML(path, filename)
