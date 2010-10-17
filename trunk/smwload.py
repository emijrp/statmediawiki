#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010 StatMediaWiki
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

import datetime
import re

import smwdb
import smwconfig
import smwget

#this is the only module that must read from the database

def load():
    loadDateRange()
    loadCategories()
    loadImages()
    loadPages()
    loadRevisions() #require startDate and endDate initialized
    loadUsers()

def loadCategories():
    smwconfig.categories.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    #capturamos el cl_to que es el título de la categoría, en vez de su ID, porque puede haber categorylinks hacia categorías cuya página no existe
    cursor.execute("SELECT cl_from, cl_to FROM %scategorylinks WHERE 1" % (smwconfig.preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        cl_from = int(row[0])
        cl_to = re.sub('_', ' ', unicode(row[1], "utf-8"))
        cl_to_ = re.sub(' ', '_', unicode(row[1], "utf-8"))

        if smwconfig.categories.has_key(cl_to_):
            smwconfig.categories[cl_to_]["pages"].append(cl_from)
        else:
            smwconfig.categories[cl_to_] = {
                "category_title": cl_to,
                "category_title_": cl_to_,
                "pages": [cl_from]
            }

    #también miramos el nm=14, para categorías creadas pero que no contienen páginas categorizadas aun
    cursor.execute("SELECT page_title FROM %spage WHERE page_namespace=14" % (smwconfig.preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        page_title = re.sub('_', ' ', unicode(row[0], "utf-8"))
        page_title_ = re.sub(' ', '_', unicode(row[0], "utf-8"))
        #solo hay un caso, que no esté, y como hablamos de una categoría sin nada dentro, la creamos con []
        if not smwconfig.categories.has_key(page_title_):
            smwconfig.categories[page_title_] = {
                "category_title": page_title,
                "category_title_": page_title_,
                "pages": []
            }

    #print categories.items()
    print "Loaded %s categories" % len(smwconfig.categories.keys())
    smwdb.destroyConnCursor(conn, cursor)

def loadDateRange():
    conn, cursor = smwdb.createConnCursor()

    if not smwconfig.preferences["startDate"]:
        cursor.execute("SELECT rev_timestamp FROM %srevision ORDER BY rev_timestamp ASC LIMIT 1" % (smwconfig.preferences["tablePrefix"]))
        a = cursor.fetchall()[0][0]
        smwconfig.preferences["startDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=0, minute=0, second=0)

    if not smwconfig.preferences["endDate"]:
        cursor.execute("SELECT rev_timestamp FROM %srevision ORDER BY rev_timestamp DESC LIMIT 1" % (smwconfig.preferences["tablePrefix"]))
        a = cursor.fetchall()[0][0]
        smwconfig.preferences["endDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=23, minute=59, second=59)

    smwdb.destroyConnCursor(conn, cursor)

def loadImages():
    smwconfig.images.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT img_name, img_user, img_user_text, img_timestamp, img_size FROM %simage WHERE 1" % (smwconfig.preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        img_name = re.sub('_', ' ', unicode(row[0], 'utf-8'))
        img_name_ = re.sub(' ', '_', unicode(row[0], 'utf-8'))
        img_user = int(row[1])
        img_user_text = re.sub('_', ' ', unicode(row[2], 'utf-8'))
        img_user_text_ = re.sub(' ', '_', unicode(row[2], 'utf-8'))
        img_timestamp = row[3]
        img_size = int(row[4])
        smwconfig.images[img_name_] = {
            "img_name": img_name,
            "img_name_": img_name_,
            "img_user": img_user,
            "img_user_text": img_user_text,
            "img_user_text_": img_user_text_,
            "img_timestamp": img_timestamp,
            "img_size": img_size,
            "img_url": smwget.getImageUrl(img_name),
        }
    print "Loaded %s images" % len(smwconfig.images.keys())
    smwdb.destroyConnCursor(conn, cursor)

def loadNamespaces():
    smwconfig.namespaces.clear() #reset
    #fix: debería cargarlos de la bbdd u otro sitio
    smwconfig.namespaces = {-2: u"Media", -1: u"Special", 0: "Main", 1: u"Talk", 2: u"User", 3: u"User talk", 4: u"Project", 5: u"Project talk", 6: u"File", 7: u"File talk", 8: u"MediaWiki", 9: u"MediaWiki talk", 10: u"Template", 11: u"Template talk", 12: u"Help", 13: u"Help talk", 14: u"Category", 15: u"Category talk"}

def loadPages():
    smwconfig.pages.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("select page_id, page_namespace, page_title, page_is_redirect, page_len, page_counter from %spage" % smwconfig.preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        page_id = int(row[0])
        page_namespace = int(row[1])
        page_title = re.sub('_', ' ', unicode(row[2], "utf-8"))
        page_title_ = re.sub(' ', '_', unicode(row[2], "utf-8"))
        page_is_redirect = int(row[3])
        page_len = int(row[4])
        page_counter = int(row[5])
        smwconfig.pages[page_id] = {
            "page_id": page_id,
            "page_namespace": page_namespace,
            "page_title": page_title,
            "page_title_": page_title_,
            "page_is_redirect": page_is_redirect,
            "page_len": page_len,
            "page_counter": page_counter, #visits
        }
    print "Loaded %s pages" % len(smwconfig.pages.keys())
    smwdb.destroyConnCursor(conn, cursor)

def loadRevisions():
    smwconfig.revisions.clear() # reset

    conn, cursor = smwdb.createConnCursor()
    cursor.execute("select rev_id, rev_page, rev_user, rev_user_text, rev_timestamp, rev_comment, rev_parent_id, old_text from %srevision, %stext where old_id=rev_text_id" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        rev_id = int(row[0])
        rev_page = int(row[1])
        rev_user = int(row[2])
        rev_user_text = unicode(re.sub('_', ' ', row[3]), "utf-8")
        rev_user_text_ = unicode(re.sub(' ', '_', row[3]), "utf-8")
        rev_timestamp = row[4]
        rev_comment = unicode(row[5].tostring(), "utf-8")
        rev_parent_id = int(row[6])
        old_text = unicode(row[7].tostring(), "utf-8")
        smwconfig.revisions[rev_id] = {
            "rev_id": rev_id, #no es un error
            "rev_page": rev_page,
            "rev_user": rev_user,
            "rev_user_text": rev_user_text,
            "rev_user_text_": rev_user_text_,
            "rev_timestamp": datetime.datetime(year=int(rev_timestamp[:4]), month=int(rev_timestamp[4:6]), day=int(rev_timestamp[6:8]), hour=int(rev_timestamp[8:10]), minute=int(rev_timestamp[10:12]), second=int(rev_timestamp[12:14])),
            "rev_comment": rev_comment,
            "rev_parent_id": rev_parent_id,
            "old_text": old_text,
            "len_diff": 0,
        }
    print "Loaded %s revisions" % len(smwconfig.revisions.keys())

    #len_diff, incremento de tamaño respecto a la versión anterior (si es negativo es decremento)
    for rev_id, rev_props in smwconfig.revisions.items():
        #que pasa con los rev_parent_id que apuntan a revisiones borradas?
        rev_parent_id = rev_props["rev_parent_id"]
        if rev_parent_id == 0: #es la primera revisión de esta página
            smwconfig.revisions[rev_id]["len_diff"] = len(rev_props["old_text"])
        elif smwconfig.revisions.has_key(rev_parent_id):
            smwconfig.revisions[rev_id]["len_diff"] = len(rev_props["old_text"]) - len(smwconfig.revisions[rev_parent_id]["old_text"])
        else:
            print "Revision", rev_parent_id, "not found"
            sys.exit()

    smwdb.destroyConnCursor(conn, cursor)

def loadUsers():
    smwconfig.users.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    queries = [
        "SELECT DISTINCT rev_user, rev_user_text FROM %srevision WHERE 1" % (smwconfig.preferences["tablePrefix"]),
        "SELECT user_id, user_name FROM %suser WHERE 1" % (smwconfig.preferences["tablePrefix"]),
    ]
    for query in queries:
        cursor.execute(query)
        result = cursor.fetchall()
        for row in result:
            user_id = int(row[0])
            user_name = re.sub('_', ' ', unicode(row[1], 'utf-8'))
            user_name_ = re.sub(' ', '_', unicode(row[1], 'utf-8'))
            if not smwconfig.users.has_key(user_id):
                smwconfig.users[user_name_] = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_name_": user_name_,
                }
    print "Loaded %s users" % len(smwconfig.users.keys())
    smwdb.destroyConnCursor(conn, cursor)
