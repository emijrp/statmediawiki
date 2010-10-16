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

#import hashlib #From python2.5
import md5
import re

import smwdb
import smwconfig

def getTotalUsers():
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT COUNT(user_id) AS count FROM %suser WHERE 1" % smwconfig.preferences["tablePrefix"])
    result = int(cursor.fetchall()[0][0])
    smwdb.destroyConnCursor(conn, cursor)
    return result

def getTotalEdits():
    conn, cursor = smwdb.createConnCursor()
    #número de usuarios a partir de las revisiones y de la tabla de usuarios, len(user.items())
    cursor.execute("SELECT COUNT(rev_id) AS count FROM %srevision WHERE 1" % smwconfig.preferences["tablePrefix"])
    result = int(cursor.fetchall()[0][0])
    smwdb.destroyConnCursor(conn, cursor)
    return result

def getTotalEditsByNamespace(namespace=0):
    conn, cursor = smwdb.createConnCursor()
    #todo: con un inner join mejor?
    cursor.execute("SELECT COUNT(rev_id) AS count FROM %srevision WHERE rev_page IN (SELECT page_id FROM %spage WHERE page_namespace=%d)" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], namespace))
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalPages():
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT COUNT(page_id) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"])
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalPagesByNamespace(namespace=0, redirects=False):
    conn, cursor = smwdb.createConnCursor()
    if redirects:
        cursor.execute("SELECT COUNT(*) AS count FROM %spage WHERE page_namespace=%d" % (namespace, smwconfig.preferences["tablePrefix"]))
    else:
        cursor.execute("SELECT COUNT(*) AS count FROM %spage WHERE page_namespace=%d AND page_is_redirect=0" % (namespace, smwconfig.preferences["tablePrefix"]))
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalBytes():
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"])
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalBytesByNamespace(namespace=0, redirects=False):
    conn, cursor = smwdb.createConnCursor()
    if redirects:
        cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE page_namespace=%d" % (namespace, smwconfig.preferences["tablePrefix"]))
    else:
        cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE page_namespace=%d AND page_is_redirect=0" % (namespace, smwconfig.preferences["tablePrefix"]))
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalVisits():
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT SUM(page_counter) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"])
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalVisitsByNamespace(namespace=0, redirects=False):
    conn, cursor = smwdb.createConnCursor()
    if redirects:
        cursor.execute("SELECT SUM(page_counter) AS count FROM %spage WHERE page_namespace=%d" % (namespace, smwconfig.preferences["tablePrefix"]))
    else:
        cursor.execute("SELECT SUM(page_counter) AS count FROM %spage WHERE page_namespace=%d AND page_is_redirect=0" % (namespace, smwconfig.preferences["tablePrefix"]))
    result = int(cursor.fetchall()[0][0])
    return result

def getTotalFiles():
    conn, cursor = smwdb.createConnCursor()
    cursor.execute("SELECT COUNT(*) AS count FROM %simage WHERE 1" % smwconfig.preferences["tablePrefix"])
    result = int(cursor.fetchall()[0][0])
    return result

def getImageUrl(img_name):
    img_name_ = re.sub(' ', '_', img_name) #espacios a _
    md5_ = md5.md5(img_name_.encode('utf-8')).hexdigest() #digest hexadecimal
    img_url = u"%s/images/%s/%s/%s" % (smwconfig.preferences["siteUrl"], md5_[0], md5_[:2], img_name_)
    return img_url

def getUserImages(user_id):
    user_images = []
    for img_name, imageprops in smwconfig.images.items():
        if imageprops["img_user"] == user_id:
            user_images.append(img_name)
    return user_images

def getUserRevisions(user_id):
    user_revisions = []

    user_name = smwconfig.users[user_id]["user_name"]
    for rev_id, rev_props in smwconfig.revisions.items():
        if user_name == rev_props["rev_user_text"]:
            user_revisions.append(rev_id)

    return user_revisions

def pagetitle2pageid(page_title=None, page_namespace=None):
    #recibe un page_title sin prefijo de espacio de nombres
    #el espacio de nombres se sabe por page_namespace
    if page_title and page_namespace:
        for page_id, page_props in smwconfig.pages.items():
            if page_props["page_namespace"] == page_namespace:
                page_title2 = page_props["page_title"]
                if page_props["page_namespace"] != 0:
                    #le quitamos el prefijo de espacio de nombres antes de comparar
                    page_title2 = ':'.join(page_title2.split(':')[1:])
                if page_title == page_title2:
                    return page_id

    return None