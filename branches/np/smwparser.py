# -*- coding: utf-8  -*-

import datetime
import sqlite3
import time
import xmlreader
import sys
import os
import tkMessageBox

def parseWikimediaXML(path, filename):
    xml = xmlreader.XmlDump('%s/%s' % (path, filename), allrevisions=True)
    
    pathsqlitedbs = '%s/sqlitedbs' % (path)
    if not os.path.exists(pathsqlitedbs):
        os.makedirs(pathsqlitedbs)
    filenamedb = '%s/%s.db' % (pathsqlitedbs, filename.split('.xml.7z')[0])
    
    if os.path.exists(filenamedb):
        print 'Ya existe un preprocesado para este proyecto'
        
        if tkMessageBox.askyesno("File exists", "A parsed file exists. Delete and re-parse?"):
            os.remove(filenamedb)
        else:
            return
    
    conn = sqlite3.connect(filenamedb)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''create table revision (title text, id integer, username text, timestamp timestamp, revisionid integer)''')
    
    limit = 10000
    c = 0
    i=0
    t1=time.time()
    tt=time.time()
    for x in xml.parse():
        timestamp = datetime.datetime(year=int(x.timestamp[0:4]), month=int(x.timestamp[5:7]), day=int(x.timestamp[8:10]), hour=int(x.timestamp[11:13]), minute=int(x.timestamp[14:16]), second=int(x.timestamp[17:19]))
        t = (x.title, x.id, x.username, timestamp, x.revisionid)
    
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
    
    # We can also close the cursor if we are done with it
    cursor.close()
    
    print 'OK!'
    tkMessageBox.showinfo("OK", "Parsing complete")

if __name__ == "__main__":
    filename = sys.argv[1]
    path = ''
    parseWikimediaXML(path, filename)
