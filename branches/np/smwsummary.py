# -*- coding: utf-8  -*-

from Tkinter import *

import sqlite3
import tkMessageBox

#TODO: que meta los numeros en un diccionario?

def summary(cursor):
    #sugerencias: páginas por nm (y separando redirects de no redirects), 
    
    revisions = 0
    pages = 0
    users = 0
    age = 0
    
    result = cursor.execute("SELECT COUNT(rev_id) AS count FROM revision WHERE 1")
    for row in result:
        revisions = row[0]
    
    result = cursor.execute("SELECT COUNT(page_id) AS count FROM page WHERE 1")
    for row in result:
        pages = row[0]
    
    result = cursor.execute("SELECT COUNT(user_name) AS count FROM user WHERE 1")
    for row in result:
        users = row[0]
    
    output= u'Users = %s\nPages = %s\nRevisions = %s' % (users, pages, revisions)
    print output
    #tkMessageBox.showinfo(title="Summary", message=output)
    
    frame = Tk()
    frame.title('Summary')
    frame.geometry('250x300+300+100')
    
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    #fix: con un label sería mejor?
    text = Text(frame, wrap=WORD, yscrollcommand=scrollbar.set)
    text.insert(INSERT, output)
    text.config(state=NORMAL) #si lo pongo en solo lectura (DISABLED), no deja copiar/pegar con ctrl-c
    text.pack()
    scrollbar.config(command=text.yview)

    #msg = Label(frame, text=output)
    #msg.pack(expand=YES, fill=BOTH)
    #msg.config(relief=SUNKEN, width=40, height=7, bg='beige')
    
def editsByRegisteredUsers(cursor=None):
    #fix esto debería estar en una tabla summary ya?
    result = cursor.execute("SELECT COUNT(revisionid) AS count FROM revision WHERE ipedit=?", (0,))
    for row in result:
        return row[0]
    return 0

def editsByAnonymousUsers(cursor=None):
    #fix esto debería estar en una tabla summary ya?
    result = cursor.execute("SELECT COUNT(revisionid) AS count FROM revision WHERE ipedit=?", (1,))
    for row in result:
        return row[0]
    return 0
