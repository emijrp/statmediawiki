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

def graph(cursor=None, range='', entity=''):
    f=open('output/file.dot', 'w')
    
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
    
    os.system('dot output/file.dot -o output/file.png -Tpng')
    print "GRAFO GUARDADO EN OUTPUT/"

def graphUserEdits():
    pass
