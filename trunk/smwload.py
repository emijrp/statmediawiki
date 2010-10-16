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

def loadImages():
    smwconfig.images = {} #reset

    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT img_name, img_user, img_user_text, img_timestamp, img_size FROM %simage WHERE 1" % (smwconfig.preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        img_name = unicode(re.sub("_", " ", row[0]), "utf-8")
        img_user = int(row[1])
        img_user_text = unicode(re.sub("_", " ", row[2]), "utf-8")
        if img_user == 0: #ip (no es normal que la subida anónima esté habilitada, pero quien sabe...)
            img_user = img_user_text
        img_timestamp = row[3]
        img_size = int(row[4])
        smwconfig.images[img_name] = {
            "img_user": img_user,
            "img_user_text": img_user_text,
            "img_timestamp": img_timestamp,
            "img_size": img_size,
            "img_url": smwget.getImageUrl(img_name),
        }
    print "Loaded %s images" % len(smwconfig.images.items())

    smwdb.destroyConnCursor(conn, cursor)

def loadUsers():
    smwconfig.users = {} #reset

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
            user_name = unicode(re.sub("_", " ", row[1]), "utf-8")
            if user_id == 0: #if ip, we use user_name (ip) as id
                user_id = user_name
            if not smwconfig.users.has_key(user_id):
                smwconfig.users[user_id] = {
                    "user_name": user_name,
                    "images": [],
                    "revisions": [],
                    "revisionsbynamespace": {"*": 0, 0: 0},
                    "bytesbynamespace": {"*": 0, 0: 0},
                }
    print "Loaded %s users" % len(smwconfig.users.items())

    #cargamos listas de images y revisiones para cada usuario
    #no puede hacerse en el bucle anterior porque getUserImages() y la otra función, llaman a users y necesitan que users esté relleno ya
    for user_id, user_props in smwconfig.users.items():
        smwconfig.users[user_id]["images"] = smwget.getUserImages(user_id)
        smwconfig.users[user_id]["revisions"] = smwget.getUserRevisions(user_id)

    #revisions by namespace
    for rev_id, rev_props in smwconfig.revisions.items():
        rev_page = rev_props["rev_page"]
        rev_user = rev_props["rev_user"]
        smwconfig.users[rev_user]["revisionsbynamespace"]["*"] += 1
        if smwconfig.pages[rev_page]["page_namespace"] == 0:
            smwconfig.users[rev_user]["revisionsbynamespace"][0] += 1

    smwdb.destroyConnCursor(conn, cursor)

def loadPages():
    smwconfig.pages = {}

    conn, cursor = smwdb.createConnCursor()
    cursor.execute("select page_id, page_namespace, page_title, page_is_redirect, page_len, page_counter from %spage" % smwconfig.preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        page_id = int(row[0])
        page_namespace = int(row[1])
        page_title = unicode(re.sub("_", " ", row[2]), "utf-8")
        if page_namespace != 0:
            page_title = u"%s:%s" % (smwconfig.namespaces[page_namespace], page_title) #fix, mejor no meterle el namespace?
        page_is_redirect = int(row[3])
        page_len = int(row[4])
        page_counter = int(row[5])
        smwconfig.pages[page_id] = {
            "page_namespace": page_namespace,
            "page_title": page_title,
            "page_is_redirect": page_is_redirect,
            "page_len": page_len,
            "page_counter": page_counter, #visits
            "revisions": [],
            "revisionsbyuserclass": {"anon": 0, "reg": 0},
            "edits": 0,
        }
    print "Loaded %s pages" % len(smwconfig.pages.items())

    #count edits per page
    for rev_id, rev_props in smwconfig.revisions.items():
        rev_page = rev_props["rev_page"]
        if smwconfig.pages.has_key(rev_page):
            smwconfig.pages[rev_page]["edits"] += 1
            smwconfig.pages[rev_page]["revisions"].append(rev_id)
            if rev_props["rev_user"] == rev_props["rev_user_text"]: #anon #todo:  tener una variable is_anon en cada revisión?
                smwconfig.pages[rev_page]["revisionsbyuserclass"]["anon"] += 1
            else:
                smwconfig.pages[rev_page]["revisionsbyuserclass"]["reg"] += 1
        else:
            print "Page", rev_page, "not found"
            sys.exit()

    smwdb.destroyConnCursor(conn, cursor)

def loadCategories():
    smwconfig.categories = {} #reset

    conn, cursor = smwdb.createConnCursor()
    #capturamos el cl_to que es el título de la categoría, en vez de su ID, porque puede haber categorylinks hacia categorías cuya página no existe
    cursor.execute("select cl_from, cl_to from %scategorylinks where 1" % smwconfig.preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        cl_from = int(row[0])
        cl_to = unicode(re.sub("_", " ", row[1]), "utf-8")

        if smwconfig.categories.has_key(cl_to):
            smwconfig.categories[cl_to].append(cl_from)
        else:
            smwconfig.categories[cl_to] = [cl_from]

    #también miramos el nm=14, para categorías creadas pero que no contienen páginas categorizadas aun
    cursor.execute("select page_title from %spage where page_namespace=14" % smwconfig.preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        page_title = unicode(re.sub("_", " ", row[0]), "utf-8")
        #solo hay un caso, que no esté, y como hablamos de una categoría sin nada dentro, la creamos con []
        if not smwconfig.categories.has_key(page_title):
            smwconfig.categories[page_title] = []

    #print categories.items()
    print "Loaded %s categories" % len(smwconfig.categories.items())

    smwdb.destroyConnCursor(conn, cursor)

def loadRevisions():
    smwconfig.revisions = {} # reset

    conn, cursor = smwdb.createConnCursor()
    cursor.execute("select rev_id, rev_page, rev_user, rev_user_text, rev_timestamp, rev_comment, rev_parent_id, old_text from %srevision, %stext where old_id=rev_text_id" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        rev_id = int(row[0])
        rev_page = int(row[1])
        rev_user = int(row[2])
        rev_user_text = unicode(re.sub("_", " ", row[3]), "utf-8")
        if rev_user == 0: #ip
            rev_user = rev_user_text
        rev_timestamp = row[4]
        rev_comment = unicode(row[5].tostring(), "utf-8")
        rev_parent_id = int(row[6])
        old_text = unicode(row[7].tostring(), "utf-8")
        smwconfig.revisions[rev_id] = {
            "rev_id": rev_id, #no es un error
            "rev_page": rev_page,
            "rev_user": rev_user,
            "rev_user_text": rev_user_text,
            "rev_timestamp": datetime.datetime(year=int(rev_timestamp[:4]), month=int(rev_timestamp[4:6]), day=int(rev_timestamp[6:8]), hour=int(rev_timestamp[8:10]), minute=int(rev_timestamp[10:12]), second=int(rev_timestamp[12:14])),
            "rev_comment": rev_comment,
            "rev_parent_id": rev_parent_id,
            "old_text": old_text,
            "len_diff": 0,
        }
    print "Loaded %s revisions" % len(smwconfig.revisions.items())

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

