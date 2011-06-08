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

from Tkinter import *

import sqlite3
import tkMessageBox

#TODO: que meta los numeros en un diccionario?

def totalEdits(cursor=None):
    result = cursor.execute("SELECT COUNT(rev_id) AS count FROM revision WHERE 1")
    for row in result:
        return row[0]
    return 0

def totalPages(cursor=None):
    result = cursor.execute("SELECT COUNT(page_id) AS count FROM page WHERE 1")
    for row in result:
        return row[0]
    return 0

def totalUsers(cursor=None):
    result = cursor.execute("SELECT COUNT(user_name) AS count FROM user WHERE 1")
    for row in result:
        return row[0]
    return 0

def summary(cursor):
    #sugerencias: páginas por nm (y separando redirects de no redirects), log events? deletes, page moves

    revisions = totalEdits(cursor=cursor)
    pages = totalPages(cursor=cursor)
    users = totalUsers(cursor=cursor)
    age = 0

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
    result = cursor.execute("SELECT COUNT(rev_id) AS count FROM revision WHERE rev_is_ipedit=?", (0,))
    for row in result:
        return row[0]
    return 0

def editsByAnonymousUsers(cursor=None):
    #fix esto debería estar en una tabla summary ya?
    result = cursor.execute("SELECT COUNT(rev_id) AS count FROM revision WHERE rev_is_ipedit=?", (1,))
    for row in result:
        return row[0]
    return 0
