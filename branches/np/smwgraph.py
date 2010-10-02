# -*- coding: utf-8  -*-

import os
import re

import numpy
import pylab

def graph(cursor=None, range='', entity=''):
    f=open('output/file.dot', 'w')
    
    print "GENERANDO GRAFO"
    a = None
    if range == 'page':
        a = cursor.execute("select username, revisionid, md5, timestamp from revision where title=? order by timestamp", (entity,))
    
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
    for id1, id2, user in relations:
        output += '"%s" -> "%s" [label="%s"];\n' % (id1, id2, user)
    
    output = 'digraph G {\n %s\n}' % (output)
    f.write(output.encode('utf-8'))
    
    f.close()
    
    os.system('dot output/file.dot -o output/file.png -Tpng')
    print "GRAFO GUARDADO EN OUTPUT/"

def graphUserEdits():
    pass
