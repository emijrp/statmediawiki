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

#todo: convertir todos los getSingleValue y sus queries en consultas a los diccionarios

def getTotalBytes():
    return sum([page_props["page_len"] for page_id, page_props in smwconfig.pages.items()])

def getTotalBytesByNamespace(namespace=0, redirects=False):
    if redirects:
        return sum([page_props["page_len"] for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace])
    else:
        return sum([page_props["page_len"] for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace and not page_props["page_is_redirect"]])

def getTotalBytesByUser(user_id=None, user_text_=None):
    if user_id:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["len_diff"] > 0])
    elif user_text_:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["len_diff"] > 0])
    assert False

def getTotalBytesByUserInNamespace(user_id=None, user_text_=None, namespace=0):
    assert user_id or user_text_
    if user_id:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["rev_page"] in getPagesByNamespace(namespace=namespace) and rev_props["len_diff"] > 0])
    elif user_text_:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["rev_page"] in getPagesByNamespace(namespace=namespace) and rev_props["len_diff"] > 0])

def getTotalBytesByUserInPage(user_id=None, user_text_=None, page_id=None):
    assert (user_id or user_text_) and page_id
    if user_id:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["rev_page"] == page_id and rev_props["len_diff"] > 0])
    elif user_text_:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["rev_page"] == page_id and rev_props["len_diff"] > 0])

def getTotalImages():
    return len(smwconfig.images)

def getTotalPages():
    return len(smwconfig.pages)

def getTotalPagesByUser(user_id=None, user_text_=None):
    #fix separar en pageseditedbyuser y pagescreatedbyuser?
    if user_id:
        return len(set([rev_props["rev_page"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id]))
    elif user_text_:
        return len(set([rev_props["rev_page"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_]))
    assert False

def getTotalRevisions():
    return len(smwconfig.revisions)

def getTotalRevisionsByNamespace(namespace=0):
    return len([rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_page"] in getPagesByNamespace(namespace=namespace)])

def getTotalRevisionsByPage(page_id=None):
    assert page_id
    return len([rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_page"] == page_id])

def getRevisionsByUser(user_id=None, user_text_=None):
    assert user_id or user_text_
    if user_id:
        return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id]
    elif user_text_:
        return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_]

def getTotalRevisionsByUser(user_id=None, user_text_=None):
    assert user_id or user_text_
    return len(getRevisionByUser(user_id=user_id, user_text_=user_text_))

def getRevisionsByUserInNamespace(user_id=None, user_text_=None, namespace=0):
    assert user_id or user_text_
    if user_id:
        return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["rev_page"] in getPagesByNamespace(namespace=namespace)]
    elif user_text_:
        return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["rev_page"] in getPagesByNamespace(namespace=namespace)]

def getTotalRevisionsByUserInNamespace(user_id=None, user_text_=None, namespace=0):
    assert user_id or user_text_
    return len(getRevisionsByUserInNamespace(user_id=user_id, user_text_=user_text_, namespace=namespace))

def getTotalUsers():
    return len(smwconfig.users)

def getPages():
    return smwconfig.pages.keys()

def getPagesByNamespace(namespace=0):
    return [page_id for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace]

def getTotalEditsByNamespace(namespace=0):
    return int(getSingleValue("SELECT COUNT(rev_id) AS count FROM %srevision WHERE rev_page IN (SELECT page_id FROM %spage WHERE page_namespace=%d)" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], namespace)))

def getTotalPagesByNamespace(namespace=0, redirects=False):
    if redirects:
        return int(getSingleValue("SELECT COUNT(*) AS count FROM %spage WHERE page_namespace=%d" % (smwconfig.preferences["tablePrefix"], namespace)))
    else:
        return int(getSingleValue("SELECT COUNT(*) AS count FROM %spage WHERE page_namespace=%d AND page_is_redirect=0" % (smwconfig.preferences["tablePrefix"], namespace)))


def getTotalVisits():
    return int(getSingleValue("SELECT SUM(page_counter) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"]))

def getTotalVisitsByNamespace(namespace=0, redirects=False):
    if redirects:
        return int(getSingleValue("SELECT SUM(page_counter) AS count FROM %spage WHERE page_namespace=%d" % (smwconfig.preferences["tablePrefix"], namespace)))
    else:
        return int(getSingleValue("SELECT SUM(page_counter) AS count FROM %spage WHERE page_namespace=%d AND page_is_redirect=0" % (smwconfig.preferences["tablePrefix"], namespace)))

def getTotalFiles():
    return int(getSingleValue("SELECT COUNT(*) AS count FROM %simage WHERE 1" % smwconfig.preferences["tablePrefix"]))

def getImageUrl(img_name):
    img_name_ = re.sub(' ', '_', img_name) #espacios a _
    md5_ = md5.md5(img_name_.encode('utf-8')).hexdigest() #digest hexadecimal
    img_url = u"%s/images/%s/%s/%s" % (smwconfig.preferences["siteUrl"], md5_[0], md5_[:2], img_name_)
    return img_url

def getImagesByUser(user_text_=None, user_id=None):
    if user_id:
        return [img_name_ for img_name_, img_props in smwconfig.images.items() if img_props["img_user"] == user_id]
    elif user_text_:
        return [img_name_ for img_name_, img_props in smwconfig.images.items() if img_props["img_user_text_"] == user_text_]


def getUsersSortedByTotalEdits():
    usersSorted = {}
    for rev_id, rev_props in smwconfig.revisions.items():
        if usersSorted.has_key(rev_props["rev_user_text_"]):
            usersSorted[rev_props["rev_user_text_"]] += 1
        else:
            usersSorted[rev_props["rev_user_text_"]] = 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()

    return list

def getUsersSortedByTotalEditsInPage(page_id=None):
    assert page_id
    usersSorted = {}
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] != page_id:
            continue
        if usersSorted.has_key(rev_props["rev_user_text_"]):
            usersSorted[rev_props["rev_user_text_"]] += 1
        else:
            usersSorted[rev_props["rev_user_text_"]] = 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()

    return list

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
