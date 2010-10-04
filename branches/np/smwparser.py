# -*- coding: utf-8  -*-

import datetime
import sqlite3
import time
import xmlreader
import sys
import os
import hashlib
import tkMessageBox

#TODO: unificar las funciones parsemywiki y parsemediawiki en la medida de lo posible, ahora mismo hay mucho código repetido
#sugerencias de tablas: una para usuarios para poder tener a mano una lista rapida con todos los usuarios para mostrar en listbox o algo así

#fix filtrar Mediawiki default (que aparece como ip)

def createDB(conn=None, cursor=None):
    cursor.execute('''create table revision (title text, id integer, username text, ipedit integer, timestamp timestamp, revisionid integer, md5 text)''')
    cursor.execute('''create table page (title text, editcount integer)''') #fix, poner si es ip basándonos en ipedit?
    cursor.execute('''create table user (username text, editcount integer)''')
    conn.commit()

def generatePageTable(conn, cursor):
    a = cursor.execute("select title, count(*) as count from revision where 1 group by title")
    c=0
    pages = []
    for row in a:
        c+=1
        pages.append([row[0], row[1]])
    
    for title, editcount in pages:
        cursor.execute('insert into page values (?,?)', (title, editcount))
    conn.commit()
    
    print "GENERADA TABLA AUXILIAR PARA PAGINAS: %d" % (c)

def generateUserTable(conn, cursor):
    a = cursor.execute("select username, count(*) as count from revision where 1 group by username")
    c=0
    users = []
    for row in a:
        c+=1
        users.append([row[0], row[1]])
    
    for user, editcount in users:
        cursor.execute('insert into user values (?,?)', (user, editcount))
    conn.commit()
    
    print "GENERADA TABLA AUXILIAR PARA USUARIOS: %d" % (c)

def generateAuxTables(conn=None, cursor=None):
    generatePageTable(conn=conn, cursor=cursor)
    generateUserTable(conn=conn, cursor=cursor)

def parseMediaWikiXMLDump(path, filename):
    xml = xmlreader.XmlDump('%s/%s' % (path, filename), allrevisions=True)
    
    pathsqlitedbs = '%s/sqlitedbs' % (path)
    if not os.path.exists(pathsqlitedbs):
        os.makedirs(pathsqlitedbs)
    filenamedb = '%s/%s.db' % (pathsqlitedbs, filename.split('.xml.')[0])
    
    if os.path.exists(filenamedb):
        print 'Ya existe un preprocesado para este proyecto'
        
        if tkMessageBox.askyesno("File exists", "A parsed file exists. Delete and re-parse?"):
            os.remove(filenamedb)
        else:
            return
    
    conn = sqlite3.connect(filenamedb)
    cursor = conn.cursor()
    
    # Create table
    createDB(conn=conn, cursor=cursor)
    
    limit = 10000
    c = 0
    i=0
    t1=time.time()
    tt=time.time()
    for x in xml.parse():
        timestamp = datetime.datetime(year=int(x.timestamp[0:4]), month=int(x.timestamp[5:7]), day=int(x.timestamp[8:10]), hour=int(x.timestamp[11:13]), minute=int(x.timestamp[14:16]), second=int(x.timestamp[17:19]))
        md5 = hashlib.md5(x.text.encode('utf-8')).hexdigest()
        ipedit = 0
        if x.ipedit:
            ipedit = 1
        t = (x.title, x.id, x.username, ipedit, timestamp, x.revisionid, md5)
    
        if not None in t and not '' in t:
            cursor.execute('insert into revision values (?,?,?,?,?,?,?)', t)
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
    
    cursor.execute("select page_title, rev_page, rev_user_text, rev_timestamp, rev_id from revision, page where page_id=rev_page")
    result = cursor.fetchall() #TODO hacerlo sin el fetchall, por si el wiki es grande
    for page_title, rev_page, rev_user_text, rev_timestamp, rev_id in result:
        timestamp = datetime.datetime(year=int(rev_timestamp[0:4]), month=int(rev_timestamp[5:7]), day=int(rev_timestamp[8:10]), hour=int(rev_timestamp[11:13]), minute=int(rev_timestamp[14:16]), second=int(rev_timestamp[17:19]))
        t = (page_title, rev_page, rev_user_text, timestamp, rev_id)
    
        if not None in t and not '' in t:
            cursor.execute('insert into revision values (?,?,?,?,?)', t)
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
