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
#pasar todos los page_id a page_props, los user_text_ y user_id a user_props (asserts e ifs) y corregir las llamadas desde los otros módulos

def pagesSortedDic():
    dic = {}
    for page_id, page_props in smwconfig.pages.items():
        dic[page_id] = 0
    return dic

def usersSortedDic():
    dic = {}
    for user_name_, user_props in smwconfig.users.items():
        dic[user_name_] = 0
    return dic

def getTotalBytes():
    return sum([page_props["page_len"] for page_id, page_props in smwconfig.pages.items()])

def getTotalBytesByCategory(category_props=None):
    assert category_props
    return sum([smwconfig.pages[page_id]["page_len"] for page_id in category_props["pages"]])

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

def getTotalBytesByUserInCategory(user_id=None, user_text_=None, category_props=None):
    assert (user_id or user_text_) and category_props
    if user_id:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["rev_page"] in category_props["pages"] and rev_props["len_diff"] > 0])
    elif user_text_:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["rev_page"] in category_props["pages"] and rev_props["len_diff"] > 0])

def getTotalBytesByUserByCategoryInNamespace(user_id=None, user_text_=None, category_props=None, namespace=0):
    assert (user_id or user_text_) and category_props
    if user_id:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["rev_page"] in category_props["pages"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace and rev_props["len_diff"] > 0])
    elif user_text_:
        return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["rev_page"] in category_props["pages"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace and rev_props["len_diff"] > 0])

def getTotalBytesByUserInNamespace(user_props=None, namespace=0):
    #hacer getBytesByUserInNamespace y llamarla no tiene mucho sentido, no? sería una lista de bytes añadidos a las páginas de ese namespace
    assert user_props
    return sum([rev_props["len_diff"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_props["user_name_"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace and rev_props["len_diff"] > 0])

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

def getTotalRevisionsByCategory(category_props=None):
    assert category_props
    return sum([getTotalRevisionsByPage(page_id=page_id) for page_id in category_props["pages"]])

def getTotalRevisionsByNamespace(namespace=0):
    return len([rev_id for rev_id, rev_props in smwconfig.revisions.items() if smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace])

def getTotalRevisionsByCategoryByNamespace(category_props=None, namespace=0):
    assert category_props
    #set para evitar contar más de una vez las ediciones de páginas que estén categorizadas en subcategorías de la actual
    #para cuando se hagan análisis recursivos por categorías
    return len(set([rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_page"] in category_props["pages"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace]))

def getTotalBytesByCategoryByNamespace(category_props=None, namespace=0):
    assert category_props
    return sum([page_props["page_len"] for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace and page_id in category_props["pages"]])

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
    return len(getRevisionsByUser(user_id=user_id, user_text_=user_text_))

def getRevisionsByUserByCategoryInNamespace(user_id=None, user_text_=None, category_props=None, namespace=0):
    assert (user_id or user_text_) and category_props
    if user_id:
        return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user"] == user_id and rev_props["rev_page"] in category_props["pages"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace]
    elif user_text_:
        return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_text_ and rev_props["rev_page"] in category_props["pages"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace]

def getTotalRevisionsByUserByCategoryInNamespace(user_id=None, user_text_=None, category_props=None, namespace=0):
    assert (user_id or user_text_) and category_props
    return len(getRevisionsByUserByCategoryInNamespace(user_id=user_id, user_text_=user_text_, category_props=category_props, namespace=namespace))

def getRevisionsByUserInNamespace(user_props=None, namespace=0):
    assert user_props
    return [rev_id for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_props["user_name_"] and smwconfig.pages[rev_props["rev_page"]]["page_namespace"] == namespace]

def getTotalRevisionsByUserInNamespace(user_props=None, namespace=0):
    assert user_props
    return len(getRevisionsByUserInNamespace(user_props=user_props, namespace=namespace))

def getTotalUsers():
    return len(smwconfig.users)

def getTotalUsersByCategory(category_props=None):
    assert category_props
    return len(set([rev_props["rev_user_text"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_page"] in category_props["pages"]]))

def getTotalUsersByPage(page_id=None):
    assert page_id
    return len(set([rev_props["rev_user_text"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_page"] == page_id]))

def getPages():
    return smwconfig.pages.keys()

def getPagesByNamespace(namespace=0):
    return [page_id for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace]

def getPagesSortedByTotalBytes():
    pagesSorted = pagesSortedDic()
    for page_id, page_props in smwconfig.pages.items():
        pagesSorted[page_id] = page_props["page_len"]

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getPagesSortedByTotalBytesByCategory(category_props=None):
    assert category_props
    pagesSorted = pagesSortedDic()
    for page_id, page_props in smwconfig.pages.items():
        if page_id not in category_props["pages"]:
            continue
        pagesSorted[page_id] = page_props["page_len"]

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getPagesSortedByTotalBytesByUser(user_props=None):
    assert user_props
    pagesSorted = pagesSortedDic()
    for rev_page, rev_props in smwconfig.revisions.items():
        if rev_props["rev_user_text_"] != user_props["user_name_"]:
            continue
        if rev_props["len_diff"] > 0:
            pagesSorted[rev_props["rev_page"]] += rev_props["len_diff"]

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getPagesSortedByTotalRevisions():
    pagesSorted = pagesSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        pagesSorted[rev_props["rev_page"]] += 1

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getPagesSortedByTotalRevisionsByCategory(category_props=None):
    assert category_props
    pagesSorted = pagesSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in category_props["pages"]:
            continue
        pagesSorted[rev_props["rev_page"]] += 1

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getPagesSortedByTotalRevisionsByUser(user_id=None, user_text_=None):
    assert user_id or user_text_
    pagesSorted = pagesSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if user_id and rev_props["rev_user"] != user_id:
            continue
        if user_text_ and rev_props["rev_user_text_"] != user_text_:
            continue
        pagesSorted[rev_props["rev_page"]] += 1

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getPagesSortedByTotalVisits():
    pagesSorted = pagesSortedDic()
    for page_id, page_props in smwconfig.pages.items():
        pagesSorted[page_id] = page_props["page_counter"]

    list = [[v, k] for k, v in pagesSorted.items()]
    list.sort()
    list.reverse()
    return list

def getTotalPagesByNamespace(namespace=0, redirects=False):
    if redirects:
        return len([page_id for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace])
    else:
        return len([page_id for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace and not page_props["page_is_redirect"]])

def getPagesByUserByNamespace(user_props=None, namespace=0, redirects=False):
    assert user_props
    if redirects:
        pageslist = [page_id for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace]
        return set([rev_props["rev_page"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_props["user_name_"] and rev_props["rev_page"] in pageslist])
    else:
        pageslist = [page_id for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace and not page_props["page_is_redirect"]]
        return set([rev_props["rev_page"] for rev_id, rev_props in smwconfig.revisions.items() if rev_props["rev_user_text_"] == user_props["user_name_"] and rev_props["rev_page"] in pageslist])

def getTotalPagesByUserByNamespace(user_props=None, namespace=0, redirects=False):
    assert user_props
    return len(getPagesByUserByNamespace(user_props=user_props, namespace=namespace, redirects=redirects))

def getTotalVisits():
    return sum([page_props["page_counter"] for page_id, page_props in smwconfig.pages.items()])

def getTotalVisitsByNamespace(namespace=0, redirects=False):
    if redirects:
        return sum([page_props["page_counter"] for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace])
    else:
        return sum([page_props["page_counter"] for page_id, page_props in smwconfig.pages.items() if page_props["page_namespace"] == namespace and not page_props["page_is_redirect"]])

def getImageUrl(img_name):
    img_name_ = re.sub(' ', '_', img_name) #espacios a _
    md5_ = md5.md5(img_name_.encode(smwconfig.preferences["codification"])).hexdigest() #digest hexadecimal
    img_url = "%s/images/%s/%s/%s" % (smwconfig.preferences["siteUrl"], md5_[0], md5_[:2], img_name_)
    return img_url

def getImagesByUser(user_text_=None, user_id=None):
    assert user_id or user_text_
    if user_id:
        return [img_name_ for img_name_, img_props in smwconfig.images.items() if img_props["img_user"] == user_id]
    elif user_text_:
        return [img_name_ for img_name_, img_props in smwconfig.images.items() if img_props["img_user_text_"] == user_text_]

def getTotalImagesByUser(user_text_=None, user_id=None):
    return len(getImagesByUser(user_text_=user_text_, user_id=user_id))

def getUsersSortedByTotalBytes():
    usersSorted = usersSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["len_diff"] <= 0:
            continue
        usersSorted[rev_props["rev_user_text_"]] += rev_props["len_diff"]

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalBytesInCategory(category_props=None):
    assert category_props
    usersSorted = usersSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in category_props["pages"]:
            continue
        if rev_props["len_diff"] <= 0:
            continue
        usersSorted[rev_props["rev_user_text_"]] += rev_props["len_diff"]

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalBytesByCategoryInNamespace(category_props=None, namespace=0):
    assert category_props
    usersSorted = usersSortedDic()
    pageslist = getPagesByNamespace(namespace=namespace)
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in pageslist:
            continue
        if rev_props["rev_page"] not in category_props["pages"]:
            continue
        if rev_props["len_diff"] <= 0:
            continue
        usersSorted[rev_props["rev_user_text_"]] += rev_props["len_diff"]

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalBytesInNamespace(namespace=0):
    usersSorted = usersSortedDic()
    pageslist = getPagesByNamespace(namespace=namespace)
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in pageslist:
            continue
        if rev_props["len_diff"] <= 0:
            continue
        usersSorted[rev_props["rev_user_text_"]] += rev_props["len_diff"]

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalBytesInPage(page_id=None):
    assert page_id

    usersSorted = usersSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] != page_id:
            continue
        if rev_props["len_diff"] <= 0:
            continue
        usersSorted[rev_props["rev_user_text_"]] += rev_props["len_diff"]

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalImages():
    usersSorted = usersSortedDic()
    for img_name_, img_props in smwconfig.images.items():
        usersSorted[img_props["img_user_text_"]] += 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalRevisions():
    usersSorted = usersSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        usersSorted[rev_props["rev_user_text_"]] += 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list


def getUsersSortedByTotalRevisionsInCategory(category_props=None):
    assert category_props
    usersSorted = usersSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in category_props["pages"]:
            continue
        usersSorted[rev_props["rev_user_text_"]] += 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalRevisionsByCategoryInNamespace(category_props=None, namespace=0):
    assert category_props
    usersSorted = usersSortedDic()
    pageslist = getPagesByNamespace(namespace=namespace)
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in pageslist:
            continue
        if rev_props["rev_page"] not in category_props["pages"]:
            continue
        usersSorted[rev_props["rev_user_text_"]] += 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalRevisionsInNamespace(namespace=0):
    usersSorted = usersSortedDic()
    pageslist = getPagesByNamespace(namespace=namespace)
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] not in pageslist:
            continue
        usersSorted[rev_props["rev_user_text_"]] += 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def getUsersSortedByTotalRevisionsInPage(page_id=None):
    assert page_id
    usersSorted = usersSortedDic()
    for rev_id, rev_props in smwconfig.revisions.items():
        if rev_props["rev_page"] != page_id:
            continue
        usersSorted[rev_props["rev_user_text_"]] += 1

    list = [[v, k] for k, v in usersSorted.items()]
    list.sort()
    list.reverse()
    return list

def pagetitle2pageid(page_title=None, page_title_=None, page_namespace=None):
    #recibe un page_title sin prefijo de espacio de nombres
    #el espacio de nombres se sabe por page_namespace
    assert (page_title or page_title_) and page_namespace
    if page_title:
        page_title_ = re.sub(' ', '_', page_title)

    for page_id, page_props in smwconfig.pages.items():
        if page_props["page_title_"] == page_title_ and page_props["page_namespace"] == page_namespace:
            return page_id

    return None
