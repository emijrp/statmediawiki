#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2012 StatMediaWiki
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

import datetime
import sqlite3
import tkMessageBox

#TODO: que meta los numeros en un diccionario?

#ideas para el resumen: total links, media ediciones/pag, total size (last page edits), total visits, total files, user with most edits, 

def totalEdits(cursor=None):
    result = cursor.execute("SELECT COUNT(rev_id) AS count FROM revision WHERE rev_is_ipedit=0")
    edits_by_reg = 0
    for row in result:
        edits_by_reg = row[0]
    
    result = cursor.execute("SELECT COUNT(rev_id) AS count FROM revision WHERE rev_is_ipedit=1")
    edits_by_unreg = 0
    for row in result:
        edits_by_unreg = row[0]
    return edits_by_reg, edits_by_unreg

def totalPages(cursor=None):
    result = cursor.execute("SELECT COUNT(page_id) AS count FROM page WHERE 1")
    for row in result:
        return row[0]
    return 0

def totalUsers(cursor=None):
    result = cursor.execute("SELECT COUNT(user_name) AS count FROM user WHERE user_is_ip=0")
    registered_users = 0
    for row in result:
        registered_users = row[0]
        
    result = cursor.execute("SELECT COUNT(user_name) AS count FROM user WHERE user_is_ip=1")
    unregistered_users = 0
    for row in result:
        unregistered_users = row[0]
    return registered_users, unregistered_users

def firstEdit(cursor=None):
    result = cursor.execute("SELECT rev_timestamp, rev_user_text FROM revision WHERE 1 ORDER BY rev_timestamp ASC LIMIT 1")
    for row in result:
        return row[0], row[1]
    return '', ''

def lastEdit(cursor=None):
    result = cursor.execute("SELECT rev_timestamp, rev_user_text FROM revision WHERE 1 ORDER BY rev_timestamp DESC LIMIT 1")
    for row in result:
        return row[0], row[1]
    return '', ''

def lifespan(firstedit='', lastedit=''):
    if firstedit and lastedit:
        return (datetime.datetime.strptime(lastedit, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(firstedit, '%Y-%m-%d %H:%M:%S')).days
    return 'Unknown'

def editSummaryUsage(cursor=None):
    result = cursor.execute("SELECT COUNT(rev_comment) FROM revision WHERE rev_comment <> '' AND rev_is_ipedit=0")
    edits_by_reg = 0
    for row in result:
        edits_by_reg = row[0]
    
    result = cursor.execute("SELECT COUNT(rev_comment) FROM revision WHERE rev_comment <> '' AND rev_is_ipedit=1")
    edits_by_unreg = 0
    for row in result:
        edits_by_unreg = row[0]
    
    return edits_by_reg, edits_by_unreg

def totalLinks(cursor=None):
    #fix recorrer la última revisión de cada página
    result = cursor.execute("SELECT SUM(page_internal_links), SUM(page_external_links), SUM(page_interwikis), SUM(page_templates) FROM page WHERE 1")
    for row in result:
        return row[0], row[1], row[2], row[3]
    return 0, 0, 0, 0

def totalSections(cursor=None):
    #fix recorrer la última revisión de cada página
    result = cursor.execute("SELECT SUM(page_sections) FROM page WHERE 1")
    for row in result:
        return row[0]
    return 0

def summary(cursor):
    #sugerencias: páginas por nm (y separando redirects de no redirects), log events? deletes, page moves
    
    pages = totalPages(cursor=cursor)
    edits_by_reg, edits_by_unreg = totalEdits(cursor=cursor)
    registered_users, unregistered_users = totalUsers(cursor=cursor)
    firstedit, fuser = firstEdit(cursor=cursor)
    lastedit, luser = lastEdit(cursor=cursor)
    summaries_by_reg, summaries_by_unreg = editSummaryUsage(cursor=cursor)
    links, external_links, interwikis, template_transclusions = totalLinks(cursor=cursor)
    sections = totalSections(cursor=cursor)
    
    output = '%s\nGlobal summary\n%s\n\n' % ('-'*60, '-'*60)
    output += 'Pages      = %d\n' % (pages)
    output += 'Revisions  = %d (total)\n' % (edits_by_reg+edits_by_unreg)
    output += '           = %d (by registered users)\n' % (edits_by_reg)
    output += '           = %d (by unregistered users)\n' % (edits_by_unreg)
    output += 'Revs/pag   = %.2f\n' % (float(edits_by_reg+edits_by_unreg)/pages)
    output += 'Users      = %d (registered users)\n' % (registered_users)
    output += '           = %d (unregistered users)\n' % (unregistered_users)
    output += 'Revs/user  = %.2f (by registered users)\n' % (float(edits_by_reg)/registered_users)
    output += '           = %.2f (by unregistered users)\n' % (edits_by_unreg and float(edits_by_unreg)/unregistered_users or 0)
    output += 'First edit = %s (User:%s)\n' % (firstedit, fuser)
    output += 'Last edit  = %s (User:%s)\n' % (lastedit, luser)
    output += 'Lifespan   = %d days\n' % (lifespan(firstedit=firstedit, lastedit=lastedit))
    output += 'Links      = %d (internal links)\n' % (links)
    output += '             %d (external links)\n' % (external_links)
    output += '             %d (interwiki links)\n' % (interwikis)
    output += '             %d (template transclusions)\n' % (template_transclusions)
    output += 'Sections   = %d\n' % (sections)
    
    output += '\n\n%s\nOther\n%s\n\n' % ('-'*60, '-'*60)
    output += 'Edit summary usage  = %d (%.2f%%) by registered users\n' % (summaries_by_reg, summaries_by_reg/(edits_by_reg/100.0))
    output += '                    = %d (%.2f%%) by unregistered users\n' % (summaries_by_unreg, summaries_by_unreg and summaries_by_unreg/(edits_by_unreg/100.0) or 0)
    output += '                    = %d (%.2f%%) by both\n' % (summaries_by_reg+summaries_by_unreg, (summaries_by_reg+summaries_by_unreg)/((edits_by_reg+edits_by_unreg)/100.0))
    
    print output
    #tkMessageBox.showinfo(title="Summary", message=output)

    frame = Tk()
    frame.title('Summary')
    frame.geometry('500x500+200+100')

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
