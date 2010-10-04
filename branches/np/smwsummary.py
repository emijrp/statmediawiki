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
    
    a = cursor.execute("select count(title) as count from page where 1")
    for row in a:
        pages = row[0]
    
    a = cursor.execute("select count(username) as count from user where 1")
    for row in a:
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
    a = cursor.execute("select count(revisionid) as count from revision where ipedit=?", (0,))
    for row in a:
        return row[0]
    return 0

def editsByAnonymousUsers(cursor=None):
    #fix esto debería estar en una tabla summary ya?
    a = cursor.execute("select count(revisionid) as count from revision where ipedit=?", (1,))
    for row in a:
        return row[0]
    return 0
