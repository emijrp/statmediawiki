# -*- coding: utf-8  -*-

import sqlite3
import tkMessageBox

def summary(cursor):
    revisions = 0
    pages = 0
    users = 0
    age = 0
    
    a = cursor.execute("select count(revisionid) as count from revision where 1")
    for row in a:
        revisions = row[0]
    
    a = cursor.execute("select count(distinct title) as count from revision where 1")
    for row in a:
        pages = row[0]
    
    a = cursor.execute("select count(distinct username) as count from revision where 1")
    for row in a:
        users = row[0]
    
    output= u'%s users have edited %s pages a total of %s times' % (users, pages, revisions)
    print output
    tkMessageBox.showinfo(title="Summary", message=output)
    
