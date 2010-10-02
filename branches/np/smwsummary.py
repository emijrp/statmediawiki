# -*- coding: utf-8  -*-

from Tkinter import *

import sqlite3
import tkMessageBox

#TODO: que meta los numeros en un diccionario?

def summary(cursor):
    #sugerencias: páginas por nm, 
    
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
    
    output= u'Users = %s\nPages = %s\nRevisions = %s' % (users, pages, revisions)
    print output
    #tkMessageBox.showinfo(title="Summary", message=output)
    
    frame = Tk()
    frame.title('Summary')
    msg = Label(frame, text=output)
    msg.pack(expand=YES, fill=BOTH)
    msg.config(relief=SUNKEN, width=40, height=7, bg='beige')
    
