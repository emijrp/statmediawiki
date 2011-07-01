#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010, 2011 StatMediaWiki
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
import md5
import random
import re
import sys

import smwdb
import smwconfig
import smwget

# This is the only module that must read from the database
# It reads a MediaWiki database with this layout: http://www.mediawiki.org/wiki/Manual:Database_layout

def load():
    loadDateRange()
    loadNamespaces()
    loadCategories()
    loadImages()
    loadPages()
    loadRevisions()
    loadUsers()

    fillPagelen()
    fillCategoryids()
    fillFullpagetitles()

def fillPagelen():
    #get the most recent edit size of the available revisions (revisions available are in the range: startDate <= revisiondate <= endDate)
    for page_id, page_props in smwconfig.pages.items():
        temprevtimestamp = None
        temppagelen = None
        for rev_id, rev_props in smwconfig.revisions.items():
            if page_id == rev_props["rev_page"]:
                if not temprevtimestamp or temprevtimestamp < rev_props["rev_timestamp"]:
                    temprevtimestamp = rev_props["rev_timestamp"]
                    temppagelen = len(rev_props["old_text"])
        smwconfig.pages[page_id]["page_len"] = temppagelen

def fillCategoryids():
    for category_title_, category_props in smwconfig.categories.items():
        ok = False #truco momentaneo
        for page_id, page_props in smwconfig.pages.items():
            if page_props["page_namespace"] == 14 and page_props["page_title_"] == category_title_:
                smwconfig.categories[category_title_]["category_id"] = page_id
                ok = True
        if not ok:
            smwconfig.categories[category_title_]["category_id"] = md5.new(category_title_.encode('utf-8')).hexdigest()

def fillFullpagetitles():
    for page_id, page_props in smwconfig.pages.items():
        smwconfig.pages[page_id]["full_page_title"] = page_props["page_namespace"] == 0 and page_props["page_title"] or '%s:%s' % (smwconfig.namespaces[page_props["page_namespace"]], page_props["page_title"])
        smwconfig.pages[page_id]["full_page_title_"] = re.sub(' ', '_', smwconfig.pages[page_id]["full_page_title"])

def loadCategories():
    smwconfig.categories.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    #capturamos el cl_to que es el título de la categoría, en vez de su ID, porque puede haber categorylinks hacia categorías cuya página no existe
    cursor.execute("SELECT cl_from, cl_to FROM %scategorylinks WHERE cl_from IN (SELECT DISTINCT rev_page FROM %srevision WHERE rev_timestamp>='%s' and rev_timestamp<='%s')" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]))
    result = cursor.fetchall()
    for row in result:
        cl_from = int(row[0])
        cl_to = re.sub('_', ' ', unicode(row[1], smwconfig.preferences['codification']))
        cl_to_ = re.sub(' ', '_', unicode(row[1], smwconfig.preferences['codification']))

        if smwconfig.categories.has_key(cl_to_):
            smwconfig.categories[cl_to_]["pages"].append(cl_from)
        else:
            smwconfig.categories[cl_to_] = {
                "category_title": cl_to,
                "category_title_": cl_to_,
                "category_id": None, #las categorías sin página creada quedarán como None
                "pages": [cl_from]
            }

    #también miramos el nm=14, para categorías creadas pero que no contienen páginas categorizadas aun
    cursor.execute("SELECT page_title FROM %spage WHERE page_namespace=14 AND page_id IN (SELECT DISTINCT rev_page FROM %srevision WHERE rev_timestamp>='%s' and rev_timestamp<='%s')" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]))
    result = cursor.fetchall()
    for row in result:
        page_title = re.sub('_', ' ', unicode(row[0], smwconfig.preferences['codification']))
        page_title_ = re.sub(' ', '_', unicode(row[0], smwconfig.preferences['codification']))
        #solo hay un caso, que no esté, y como hablamos de una categoría sin nada dentro, la creamos con []
        if not smwconfig.categories.has_key(page_title_):
            smwconfig.categories[page_title_] = {
                "category_title": page_title,
                "category_title_": page_title_,
                "category_id": None, #las categorías sin página creada quedarán como None
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
        #if no end date, get now
        now = datetime.datetime.now()
        smwconfig.preferences["endDate"] = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second)

    #conversion to MediaWiki format
    smwconfig.preferences["startDateMW"] = smwconfig.preferences["startDate"].strftime('%Y%m%d%H%M%S')
    smwconfig.preferences["endDateMW"] =  enddate = smwconfig.preferences["endDate"].strftime('%Y%m%d%H%M%S')

    smwdb.destroyConnCursor(conn, cursor)

def loadImages():
    smwconfig.images.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT img_name, img_user, img_user_text, img_timestamp, img_size FROM %simage WHERE img_timestamp>='%s' AND img_timestamp<='%s'" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]))
    result = cursor.fetchall()
    for row in result:
        img_name = re.sub('_', ' ', unicode(row[0], smwconfig.preferences['codification']))
        img_name_ = re.sub(' ', '_', unicode(row[0], smwconfig.preferences['codification']))
        img_user = int(row[1])
        img_user_text = re.sub('_', ' ', unicode(row[2], smwconfig.preferences['codification']))
        img_user_text_ = re.sub(' ', '_', unicode(row[2], smwconfig.preferences['codification']))
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
    smwconfig.namespaces = {-2: "Media", -1: "Special", 0: "Main", 1: "Talk", 2: "User", 3: "User talk", 4: "Project", 5: "Project talk", 6: "File", 7: "File talk", 8: "MediaWiki", 9: "MediaWiki talk", 10: "Template", 11: "Template talk", 12: "Help", 13: "Help talk", 14: "Category", 15: "Category talk"}

def loadPages():
    smwconfig.pages.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT page_id, page_namespace, page_title, page_is_redirect, page_counter FROM %spage WHERE page_id IN (SELECT DISTINCT rev_page FROM %srevision WHERE rev_timestamp>='%s' and rev_timestamp<='%s')" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]))
    result = cursor.fetchall()
    for row in result:
        page_id = int(row[0])
        page_namespace = int(row[1])
        page_title = re.sub('_', ' ', unicode(row[2], smwconfig.preferences['codification']))
        page_title_ = re.sub(' ', '_', unicode(row[2], smwconfig.preferences['codification']))
        page_is_redirect = int(row[3])
        page_counter = int(row[4])
        smwconfig.pages[page_id] = {
            "page_id": page_id,
            "page_namespace": page_namespace,
            "page_title": page_title,
            "page_title_": page_title_,
            "full_page_title": None,
            "full_page_title_": None,
            "page_is_redirect": page_is_redirect,
            "page_len": None, # do not use the value in the database, it is calculated with filledPagelen()
            "page_counter": page_counter, #visits
        }
    print "Loaded %s pages" % len(smwconfig.pages.keys())
    smwdb.destroyConnCursor(conn, cursor)

def loadRevisions():
    smwconfig.revisions.clear() # reset

    conn, cursor = smwdb.createConnCursor()

    cursor.execute("SELECT rev_id, rev_page, rev_user, rev_user_text, rev_timestamp, rev_comment, rev_parent_id, old_text FROM %srevision, %stext WHERE old_id=rev_text_id AND rev_timestamp>='%s' AND rev_timestamp<='%s'" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]))
    result = cursor.fetchall()
    for row in result:
        rev_id = int(row[0])
        rev_page = int(row[1])
        rev_user = int(row[2])
        rev_user_text = unicode(re.sub('_', ' ', row[3]), smwconfig.preferences['codification'])
        rev_user_text_ = unicode(re.sub(' ', '_', row[3]), smwconfig.preferences['codification'])
        rev_timestamp = row[4]
        try: #python 2.4.2 vs 2.6?
            row[5] = row[5].tostring()
        except:
            pass
        rev_comment = unicode(row[5], smwconfig.preferences['codification'])
        rev_parent_id = int(row[6])
        try:
            row[7] = row[7].tostring()
        except:
            pass
        old_text = unicode(row[7], smwconfig.preferences['codification'])
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
            #si la edición anterior no existe o fue borrada, contamos como que todo el texto es nuevo
            #todo: pasa cuando se usan rangos -startdate y -enddate?
            smwconfig.revisions[rev_id]["len_diff"] = len(rev_props["old_text"])
            #print "Revision", rev_parent_id, "not found"
            #sys.exit()

    smwdb.destroyConnCursor(conn, cursor)

def loadUsers():
    smwconfig.users.clear() #reset
    conn, cursor = smwdb.createConnCursor()
    queries = [
        "SELECT DISTINCT rev_user, rev_user_text FROM %srevision WHERE rev_timestamp>='%s' AND rev_timestamp<='%s'" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]),
        "SELECT user_id, user_name FROM %suser WHERE user_registration>='%s' AND user_registration<='%s'" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]), #for user registered but which do not edit
        "SELECT img_user, img_user_text FROM %simage WHERE img_timestamp>='%s' AND img_timestamp<='%s'" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"]), #for users which upload but do not edit

    ]
    for query in queries:
        cursor.execute(query)
        result = cursor.fetchall()
        for row in result:
            user_id = int(row[0])
            user_name = re.sub('_', ' ', unicode(row[1], smwconfig.preferences['codification']))
            user_name_ = re.sub(' ', '_', unicode(row[1], smwconfig.preferences['codification']))
            if not smwconfig.users.has_key(user_name_):
                smwconfig.users[user_name_] = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_name_": user_name_, #not an error
                }
    print "Loaded %s users" % len(smwconfig.users.keys())
    smwdb.destroyConnCursor(conn, cursor)
