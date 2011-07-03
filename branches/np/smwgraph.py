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

import os
import re

import numpy
import pylab

def graphUserMessages(cursor=None):
    #fix como evitar que alguien que edita varias veces seguidas (corrigiendo typos) en poco tiempo contabilice como varios mensajes? mejor un mensaje = editado en 1 día?
    #descartar mensajes enviados por IPs ?
    #descartar ediciones en la página de uno mismo?
    #fix colorear los usuarios que reciben más mensajes (son más importantes en la comunidad)
    #fix poner a filename el prefijo con el nombre del project, para no sobreescribir grafos de otros
    
    result = cursor.execute("SELECT rev_user_text, rev_title FROM revision WHERE 1") #fix generalizar usando namespace 3
    messages = {}
    for row in result:
        sender = row[0]
        target = row[1]
        if not re.search(ur'(?im)^(Usuario Discusión|Usuario Conversación|User talk):.+$', target):
            continue
        target = ':'.join(target.split(':')[1:]) #removing namespace prefix
        target = target.split('/')[0] #removing /Archivo 2009, etc
        
        #discarding stuff
        if sender == target:
            continue
        if re.search(ur'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', sender) or re.search(ur'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', target):
            continue
        
        if messages.has_key(sender):
            if messages[sender].has_key(target):
                messages[sender][target] += 1
            else:
                messages[sender][target] = 1
        else:
            messages[sender] = {target: 1}
    
    print messages.items()
    
    output = ''
    for sender, targets in messages.items():
        for target, times in targets.items():
            if times >= 2: #fix limite demasiado bajo? dejar los X nodos más habladores?
                output += '"%s" -> "%s" [label="%s"];\n' % (sender, target, times)
    
    output = 'digraph G {\n size="150,150" \n%s\n}' % (output)
    
    filename = 'usermessagesgraph'
    f=open('output/%s.dot' % filename, 'w')
    
    print "GENERANDO GRAFO"
    
    f.write(output.encode('utf-8'))
    
    f.close()
    
    os.system('dot output/%s.dot -o output/%s.png -Tpng' % (filename, filename))
    print "GRAFO GUARDADO EN OUTPUT/"

def graphPageHistory(cursor=None, range='', entity=''):
    filename = 'pagehistorygraph'
    f=open('output/%s.dot' % filename, 'w')
    
    print "GENERANDO GRAFO"
    a = None
    if range == 'page':
        a = cursor.execute("select rev_user_text, rev_id, rev_text_md5, rev_timestamp from revision where rev_page in (select page_id from page where page_title=?) order by rev_timestamp", (entity,))
    
    if not a:
        return
    
    md5s = {}
    relations = []
    previd = ''
    user = ''
    currentid = 'Start'
    for row in a:
        username = row[0]
        revisionid = row[1]
        md5 = row[2]
        timestamp = row[3]
        
        previd = currentid
        user = username
        currentid = revisionid
        if md5s.has_key(md5): #es una reversion
            currentid = md5s[md5]['id']
        else:
            md5s[md5] = {}
            md5s[md5]['id'] = revisionid
            md5s[md5]['user'] = username
        
        relations.append([previd, currentid, user])
    
    output = ''
    c=0
    for id1, id2, user in relations:
        c+=1
        if c!=len(relations):
            output += '"%s" -> "%s" [label="%s"];\n' % (id1, id2, user)
        else:
            output += '"%s" -> "%s" [label="LAST EDIT: %s"];\n' % (id1, id2, user)
    
    output = 'digraph G {\n size="150,150" \n%s\n}' % (output)
    f.write(output.encode('utf-8'))
    
    f.close()
    
    os.system('dot output/%s.dot -o output/%s.png -Tpng' % (filename, filename))
    print "GRAFO GUARDADO EN OUTPUT/"

def graphUserEdits():
    pass
