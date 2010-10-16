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
import random
import re
import sys

import smwdb
import smwconfig
import smwcsv
import smwget
import smwhtml
import smwplot

def generateAnalysis():
    generatePagesAnalysis()
    generateCategoriesAnalysis()
    generateUsersAnalysis()
    generateGeneralAnalysis() #necesita el useranalysis antes, para llenar los bytes

def generadorColumnaFechas(startDate, delta=datetime.timedelta(days=1)):
    # Generamos una columna virtual con fechas a partir de una fecha
    # determinada, con un salto determinado entre elementos (por omision,
    # un dia)
    currentDate = startDate
    while True:
        yield currentDate
        currentDate += delta

def generateTimeActivity(timesplit, type, fileprefix, conds, headers, user_id=None, page_id=None):
    results = {}

    conn, cursor = smwdb.createConnCursor()
    for cond in conds:
        cursor.execute("SELECT %s(rev_timestamp) AS time, COUNT(rev_id) AS count FROM %srevision INNER JOIN %spage ON rev_page=page_id WHERE %s GROUP BY time ORDER BY time" % (timesplit, smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], cond))
        result = cursor.fetchall()
        results[cond] = {}
        for timestamp, edits in result:
            if timesplit in ["dayofweek", "month"]:
                timestamp = timestamp - 1
            results[cond][str(timestamp)] = str(edits)

    headers = [timesplit] + headers
    fileprefix = "%s_%s" % (fileprefix, timesplit)
    rows = []
    if timesplit == "hour":
        range_ = range(24)
    elif timesplit == "dayofweek":
        range_ = range(7)
    elif timesplit == "month":
        range_ = range(12)

    row0=[]
    row1=[]
    row2=[]
    row3=[]
    for period in range_:
        period  = str(period)
        row0.append(period)
        cond0 = "0"
        cond1 = "0"
        cond2 = "0"
        if results[conds[0]].has_key(period):
            cond0 = results[conds[0]][period]
        row1.append(cond0)
        if results[conds[1]].has_key(period):
            cond1 = results[conds[1]][period]
        row2.append(cond1)
        if results[conds[2]].has_key(period):
            cond2 = results[conds[2]][period]
        row3.append(cond2)
    rows=[row0, row1, row2, row3]

    title = ""
    if type=="general":
        if timesplit == "hour":
            title = u"Hour activity in %s" % smwconfig.preferences["siteName"]
        elif timesplit == "dayofweek":
            title = u"Day of week activity in %s" % smwconfig.preferences["siteName"]
        elif timesplit == "month":
            title = u"Month activity in %s" % smwconfig.preferences["siteName"]
    elif type == "users":
        user_name = smwconfig.users[user_id]["user_name"]
        if timesplit == "hour":
            title = u"Hour activity by %s" % user_name
        elif timesplit == "dayofweek":
            title = u"Day of week activity by %s" % user_name
        elif timesplit == "month":
            title = u"Month activity by %s" % user_name
    elif type == "pages":
        page_title = smwconfig.pages[page_id]["page_title"]
        if timesplit == "hour":
            title = u"Hour activity in %s" % page_title
        elif timesplit == "dayofweek":
            title = u"Day of week activity in %s" % page_title
        elif timesplit == "month":
            title = u"Month activity in %s" % page_title

    # Print rows
    smwcsv.printCSV(type=type, subtype="activity", fileprefix=fileprefix,
             headers=headers, rows=rows)
    smwplot.printGraphTimeActivity(type=type, fileprefix=fileprefix, title=title,
                           headers=headers, rows=rows)

    smwdb.destroyConnCursor(conn, cursor)

def generateGeneralTimeActivity():
    conds = ["1", "page_namespace=0", "page_namespace=1"] # artículo o todas
    headers = ["Edits (all pages)", "Edits (only articles)", "Edits (only articles talks)"]
    generateTimeActivity(timesplit="hour", type="general", fileprefix="general", conds=conds, headers=headers)
    generateTimeActivity(timesplit="dayofweek", type="general", fileprefix="general", conds=conds, headers=headers)
    generateTimeActivity(timesplit="month", type="general", fileprefix="general", conds=conds, headers=headers)

def generatePagesTimeActivity(page_id):
    page_title = smwconfig.pages[page_id]["page_title"] #todo namespaces
    conds = ["1", "rev_user=0", "rev_user!=0"] #todas, anónimas o registrados
    headers = ["Edits in %s (all users)" % page_title, "Edits in %s (only anonymous users)" % page_title, "Edits in %s (only registered users)" % page_title]
    generateTimeActivity(timesplit="hour", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(timesplit="dayofweek", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(timesplit="month", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)

def generateCategoriesTimeActivity(page_id):
    category_title = ':'.join(smwconfig.pages[page_id]["page_title"].split(':')[1:]) #todo namespaces
    conds2 = ["1", "rev_user=0", "rev_user!=0"] #todas, anónimas o registrados
    conds = []
    for cond in conds2:
        conds.append("%s and rev_page in (select cl_from from categorylinks where cl_to='%s')" % (cond, re.sub(' ', '_', category_title).encode('utf-8'))) #fix cuidado con nombres de categorías con '
    headers = ["Edits in category %s (all users)" % category_title, "Edits in category %s (only anonymous users)" % category_title, "Edits in category %s (only registered users)" % category_title]
    generateTimeActivity(timesplit="hour", type="categories", fileprefix="category_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(timesplit="dayofweek", type="categories", fileprefix="category_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(timesplit="month", type="categories", fileprefix="category_%d" % page_id, conds=conds, headers=headers, page_id=page_id)

def generateUsersTimeActivity(user_id):
    user_name = smwconfig.users[user_id]["user_name"]
    if user_name == user_id: #ip
        conds = ["rev_user_text='%s'" % user_id, "page_namespace=0 and rev_user_text='%s'" % user_id, "page_namespace=1 and rev_user_text='%s'" % user_id] # artículo o todas, #todo añadir escape() para comillas?
    else:
        conds = ["rev_user=%d" % user_id, "page_namespace=0 and rev_user=%d" % user_id, "page_namespace=1 and rev_user=%d" % user_id] # artículo o todas
    headers = ["Edits by %s (all pages)" % user_name, "Edits by %s (only articles)" % user_name, "Edits by %s (only articles talks)" % user_name]
    generateTimeActivity(timesplit="hour", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)
    generateTimeActivity(timesplit="dayofweek", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)
    generateTimeActivity(timesplit="month", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)

def generateCloud(type, user_id=None, page_id=None, category_id=None, page_ids=[]):
    cloud = {}

    for rev_id, rev_props in smwconfig.revisions.items():
        if type == "users":
            if user_id:
                if rev_props["rev_user"] != user_id:
                    continue
            else:
                print u"Llamada a función tipo users sin user_id"
                sys.exit()
        elif type == "pages":
            if page_id:
                if rev_props["rev_page"] != page_id:
                    continue
            else:
                print u"Llamada a función tipo pages sin page_id"
                sys.exit()
        elif type == "categories":
            if category_id: #no ponemos and page_ids, puesto que puede ser una categoría vacía
                if rev_props["rev_page"] not in page_ids:
                    continue
            else:
                print u"Llamada a función tipo categories sin category_id"
                sys.exit()

        comment = rev_props["rev_comment"].lower().strip()
        comment = re.sub(ur"[\[\]\=\,\{\}\|\:\;\"\'\?\¿\/\*\(\)\<\>\+\.\-\#\_\&]", ur" ", comment) #no commas, csv
        comment = re.sub(ur"  +", ur" ", comment)
        tags = comment.split(" ")
        for tag in tags:
            if len(tag)<4: #unuseful tags filter
                continue
            if cloud.has_key(tag):
                cloud[tag] += 1
            else:
                cloud[tag] = 1

    cloudList = []
    for tag, times in cloud.items():
       cloudList.append([times, tag])

    cloudList.sort()
    cloudList.reverse()

    # header = ['word', 'frequency']
    # rows = []
    # c = 0

    # for times, tag in cloudList:
    #     c+=1
    #     if c>50:
    #         break
    #     rows.append([tag, str(times)])

    limit = 50

    minSize = 100 #min fontsize
    maxSize = 300 #max fontsize
    maxTimes = 0
    minTimes = 999999999
    for times, tag in cloudList[:limit]:
        if maxTimes<times:
            maxTimes = times
        if minTimes>times:
            minTimes = times

    output = u""
    cloudListShuffle = cloudList[:limit]
    random.shuffle(cloudListShuffle)
    for times, tag in cloudListShuffle:
        if maxTimes - minTimes > 0:
            fontsize = 100 + ((times - minTimes) * (maxSize - minSize)) / (maxTimes - minTimes)
        else:
            fontsize = 100 + (maxSize - minSize ) / 2
        output += u"""<span style="font-size: %s%%">%s</span> &nbsp;&nbsp;&nbsp;""" % (fontsize, tag)

    if not output:
        output += u"This user has made no comments in edits."

    return output

def generateGeneralCloud():
    return generateCloud(type="general")

def generateUsersCloud(user_id):
    return generateCloud(type="users", user_id=user_id)

def generatePagesCloud(page_id):
    return generateCloud(type="pages", page_id=page_id)

def generateCategoriesCloud(category_id, page_ids):
    return generateCloud(type="categories", category_id=category_id, page_ids=page_ids)

def generateContentEvolution(type, user_id=None, page_id=None, category_id=None, page_ids=[]):
    fecha = smwconfig.preferences["startDate"]
    fechaincremento = datetime.timedelta(days=1)
    graph1 = []
    graph2 = []
    graph3 = []
    count1 = 0
    count2 = 0
    count3 = 0
    while fecha < smwconfig.preferences["endDate"]:
        for rev_id, rev_props in smwconfig.revisions.items():
            if type == "general":
                pass #nos interesan todas
            elif type == "users":
                if not user_id:
                    print "Error: no hay user_id"
                    sys.exit()
                if rev_props["rev_user"] != user_id:
                    continue #nos la saltamos, no es de este usuario
            elif type == "pages":
                if not page_id:
                    print "Error: no hay page_id"
                    sys.exit()
                if rev_props["rev_page"] != page_id:
                    continue #nos la saltamos, no es de esta página
            elif type == "categories":
                if not category_id: #no poner not page_ids, ya que la categoría puede estar vacía y no tener page_id de página alguna
                    print "Error: no hay category_id"
                    sys.exit()
                if rev_props["rev_page"] not in page_ids:
                    continue #nos la saltamos, esta revisión no es de una página de esta categoría

            if rev_props["rev_timestamp"] < fecha and rev_props["rev_timestamp"] >= fecha - fechaincremento: # 00:00:00 < fecha < 23:59:59
                rev_page = rev_props["rev_page"]
                if type == "general":
                    #más adelante quizás convenga poner la evolución del contenido según anónimos y registrados, para el caso general
                    if smwconfig.pages[rev_page]["page_namespace"] == 0:
                        count2 += rev_props["len_diff"]
                    if smwconfig.pages[rev_page]["page_namespace"] == 1:
                        count3 += rev_props["len_diff"]
                    #evolución de todas las páginas
                    count1 += rev_props["len_diff"]
                elif type == "pages" or type == "categories":
                    if rev_props["rev_user"] == rev_props["rev_user_text"]: #anon, #todo: poner una variable is_anon para evitar esta comparación?
                        count2 += rev_props["len_diff"]
                    else:
                        count3 += rev_props["len_diff"]
                    count1 += rev_props["len_diff"]
                elif type == "users":
                    if rev_props["len_diff"] < 1:
                        #conv: solo contamos las diferencias positivas para los usuarios, de momento
                        #para el global y las páginas, sí hay retrocesos
                        continue
                    if smwconfig.pages[rev_page]["page_namespace"] == 0:
                        count2 += rev_props["len_diff"]
                    if smwconfig.pages[rev_page]["page_namespace"] == 1:
                        count3 += rev_props["len_diff"]
                    #evolución de todas las páginas
                    count1 += rev_props["len_diff"]

        graph1.append(count1)
        graph2.append(count2)
        graph3.append(count3)

        fecha += fechaincremento

    if type == "users":
        smwconfig.users[user_id]["bytesbynamespace"]["*"] = count1
        smwconfig.users[user_id]["bytesbynamespace"][0] = count2

    title = u""
    fileprefix = u""
    owner = u""
    if type == "general":
        title = u"Content evolution in %s" % smwconfig.preferences["siteName"]
        fileprefix = "general"
        owner = smwconfig.preferences["siteName"]
    elif type == "users":
        user_name = smwconfig.users[user_id]["user_name"]
        title = u"Content evolution by %s" % user_name
        fileprefix = "user_%s" % user_id
        owner = user_name
    elif type == "pages":
        page_title = smwconfig.pages[page_id]["page_title"]
        title = u"Content evolution in %s" % page_title
        fileprefix = "page_%s" % page_id
        owner = page_title
    elif type == "categories":
        category_title = smwconfig.pages[category_id]["page_title"]
        title = u"Content evolution for pages in %s" % category_title
        fileprefix = "category_%s" % category_id
        owner = category_title

    if type == "pages" or type == "categories":
        headers = ["Date", "%s content (all users)" % owner, "%s content (only anonymous users)" % owner, "%s content (only registered users)" % owner]
    else:
        headers = ["Date", "%s content (all pages)" % owner, "%s content (only articles)" % owner, "%s content (only articles talks)" % owner]

    if type == "users" and smwconfig.preferences["anonymous"]:
        pass #no print graph
    else:
        smwcsv.printCSV(type=type, subtype="content_evolution", fileprefix=fileprefix,
                 headers=headers,
                 rows=[generadorColumnaFechas(smwconfig.preferences["startDate"]),
                       graph1, graph2, graph3])
        smwplot.printGraphContentEvolution(type=type, fileprefix=fileprefix,
                                   title=title, headers=headers,
                                   rows=[graph1, graph2, graph3])

def generateGeneralContentEvolution():
    generateContentEvolution(type="general")

def generateUsersContentEvolution(user_id):
    generateContentEvolution(type="users", user_id=user_id)

def generatePagesContentEvolution(page_id):
    generateContentEvolution(type="pages", page_id=page_id)

def generateCategoriesContentEvolution(category_id, page_ids):
    generateContentEvolution(type="categories", category_id=category_id, page_ids=page_ids)

def generateUsersTable():
    output = u"""<table>
    <tr><th>#</th><th>User</th><th>Edits</th><th>Edits in articles</th><th>Bytes added</th><th>Bytes added in articles</th><th>Uploads</th></tr>"""

    sortedUsers = [] #by edits

    edits = 0
    editsinarticles = 0
    bytes = 0
    bytesinarticles = 0
    uploads = 0
    for user_id, user_props in smwconfig.users.items():
        edits += user_props["revisionsbynamespace"]["*"]
        editsinarticles += user_props["revisionsbynamespace"][0]
        bytes += user_props["bytesbynamespace"]["*"]
        bytesinarticles += user_props["bytesbynamespace"][0]
        uploads += len(user_props["images"])
        sortedUsers.append([user_props["revisionsbynamespace"]["*"], user_id])
    sortedUsers.sort()
    sortedUsers.reverse()

    c = 1
    for revisionsNumber, user_id in sortedUsers:
        user_props = smwconfig.users[user_id]
        edits_percent = user_props["revisionsbynamespace"]["*"] / (edits / 100.0)
        editsinarticles_percent = user_props["revisionsbynamespace"][0] / (editsinarticles / 100.0)
        bytes_percent = user_props["bytesbynamespace"]["*"] / (bytes / 100.0)
        bytesinarticles_percent = user_props["bytesbynamespace"][0] / (bytesinarticles / 100.0)
        if smwconfig.preferences["anonymous"]:
            output += u"""<tr><td>%s</td><td>%s</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s</td></tr>\n""" % (c, user_props["user_name"], user_props["revisionsbynamespace"]["*"], edits_percent, user_props["revisionsbynamespace"][0], editsinarticles_percent, user_props["bytesbynamespace"]["*"], bytes_percent, user_props["bytesbynamespace"][0], bytesinarticles_percent, len(user_props["images"]))
        else:
            output += u"""<tr><td>%s</td><td><a href="html/users/user_%s.html">%s</a></td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td><a href="html/users/user_%s.html#uploads">%s</a></td></tr>\n""" % (c, user_id, user_props["user_name"], user_props["revisionsbynamespace"]["*"], edits_percent, user_props["revisionsbynamespace"][0], editsinarticles_percent, user_props["bytesbynamespace"]["*"], bytes_percent, user_props["bytesbynamespace"][0], bytesinarticles_percent, user_id, len(user_props["images"]))
        c += 1

    output += u"""<tr><td></td><td>Total</td><td>%s (100%%)</td><td>%s (100%%)</td><td>%s<sup>[<a href="#note1">note 1</a>]</sup> (100%%)</td><td>%s<sup>[<a href="#note1">note 1</a>]</sup> (100%%)</td><td>%s</td></tr>\n""" % (edits, editsinarticles, bytes, bytesinarticles, uploads)
    output += u"""</table>"""
    output += u"""<ul><li id="note1">Note 1: This figure can be greater than the total bytes in the wiki, as byte erased are not discounted in this ranking.</li></ul>"""

    return output

def generatePagesTable():
    output = u"""<table>
    <tr><th>#</th><th>Page</th><th>Namespace</th><th>Edits</th><th>Bytes</th><th>Visits</th></tr>"""

    sortedPages = [] #by edits

    edits = 0
    bytes = 0
    visits = 0
    for page_id, page_props in smwconfig.pages.items():
        edits += page_props["edits"]
        bytes += page_props["page_len"]
        visits += page_props["page_counter"]
        sortedPages.append([page_props["edits"], page_id])
    sortedPages.sort()
    sortedPages.reverse()

    c = 1
    for page_edits, page_id in sortedPages:
        page_props = smwconfig.pages[page_id]
        edits_percent = page_props["edits"] / (edits / 100.0)
        bytes_percent = page_props["page_len"] / (bytes / 100.0)
        visits_percent = page_props["page_counter"] / (visits / 100.0)
        output += u"""<tr><td>%s</td><td><a href="html/pages/page_%s.html">%s</a></td><td>%s</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td></tr>\n""" % (c, page_id, page_props["page_title"], smwconfig.namespaces[page_props["page_namespace"]], page_props["edits"], edits_percent, page_props["page_len"], bytes_percent, page_props["page_counter"], visits_percent)
        c += 1

    output += """<tr><td></td><td>Total</td><td></td><td>%s (100%%)</td><td>%s (100%%)</td><td>%s (100%%)</td></tr>\n""" % (edits, bytes, visits)
    output += """</table>"""

    return output

def generateCategoriesTable():
    output = u"""<table>
    <tr><th>#</th><th>Category</th><th>Pages</th><th>Edits</th><th>Bytes</th><th>Visits</th></tr>"""

    sortedCategories = [] #by edits

    all_categorised_page_ids = set()
    for category_title, page_ids in smwconfig.categories.items():
        category_id = smwget.pagetitle2pageid(page_title=category_title, page_namespace=14)
        if category_id: #si la página de la categoría existe
            [all_categorised_page_ids.add(i) for i in page_ids] #a set to avoid dupes

    totaledits = 0
    totalbytes = 0
    totalvisits = 0
    for page_id, page_props in smwconfig.pages.items():
        if page_id in all_categorised_page_ids: #for the totals, only count categorised pages info
            totaledits += page_props["edits"]
            totalbytes += page_props["page_len"]
            totalvisits += page_props["page_counter"]
    totalpages = len(all_categorised_page_ids)

    for category_title, page_ids in smwconfig.categories.items():
        sortedCategories.append([len(page_ids), category_title])
    sortedCategories.sort()
    sortedCategories.reverse()

    c = 1
    for numpages, category_title in sortedCategories:
        category_id = smwget.pagetitle2pageid(page_title=category_title, page_namespace=14)
        if not category_id: #categorías que contienen páginas pero que no tienen página creada, por lo tanto no tienen page_id
            continue

        #acumulado para las páginas de esta categoría
        numedits = 0
        numbytes = 0
        numvisits = 0
        page_ids = smwconfig.categories[category_title]
        for page_id, page_props in smwconfig.pages.items():
            if page_id in page_ids:
                numedits += page_props["edits"]
                numbytes += page_props["page_len"]
                numvisits += page_props["page_counter"]

        numpagespercent = 0
        if totalpages > 0:
            numpagespercent = numpages/(totalpages/100.0)
        numeditspercent = 0
        if totaledits > 0:
            numeditspercent = numedits/(totaledits/100.0)
        numbytespercent = 0
        if totalbytes > 0:
            numbytespercent = numbytes/(totalbytes/100.0)
        numvisitspercent = 0
        if totalvisits > 0:
            numvisitspercent = numvisits/(totalvisits/100.0)

        output += u"""<tr><td>%d</td><td><a href="html/categories/category_%s.html">%s</a></td><td>%d (%.1f%%)</td><td>%d (%.1f%%)</td><td>%d (%.1f%%)</td><td>%d (%.1f%%)</td></tr>\n""" % (c, category_id, category_title, numpages, numpagespercent, numedits, numeditspercent, numbytes, numbytespercent, numvisits, numvisitspercent)
        c += 1

    output += """<tr><td></td><td>Total</td><td>%d (100%%)</td><td>%d (100%%)</td><td>%d (100%%)</td><td>%d (100%%)</td></tr>\n""" % (totalpages, totaledits, totalbytes, totalvisits)
    output += """</table>"""
    output += """<center>Due to some pages can be contained in various categories, the sum of the colums can be different to the total row</center>"""

    return output

def generateUsersMostEditedTable(user_id):
    output = u"""<table>
    <tr><th>#</th><th>Page</th><th>Namespace</th><th>Edits</th></tr>"""

    most_edited = {}
    for rev_id in smwconfig.users[user_id]["revisions"]:
        rev_page = smwconfig.revisions[rev_id]["rev_page"]
        if most_edited.has_key(rev_page):
            most_edited[rev_page] += 1
        else:
            most_edited[rev_page] = 1

    most_edited_list = []
    for rev_page, edits in most_edited.items():
        most_edited_list.append([edits, rev_page])
    most_edited_list.sort()
    most_edited_list.reverse()

    c = 0
    for edits, rev_page in most_edited_list:
        c += 1
        page_title = smwconfig.pages[rev_page]["page_title"]
        page_namespace = smwconfig.pages[rev_page]["page_namespace"]
        #to avoid zero division
        editspercent = 0
        if smwconfig.users[user_id]["revisionsbynamespace"]["*"] > 0:
            editspercent = edits/(smwconfig.users[user_id]["revisionsbynamespace"]["*"]/100.0)
        output += u"""<tr><td>%s</td><td><a href="../pages/page_%s.html">%s</a></td><td>%s</td><td><a href="%s/index.php?title=%s&amp;action=history">%d (%.1f%%)</a></td></tr>\n""" % (c, rev_page, page_title, smwconfig.namespaces[page_namespace], smwconfig.preferences["siteUrl"], page_title, edits, editspercent)
    output += u"""<tr><td></td><td>Total</td><td></td><td>%d (100%%)</td></tr>""" % (smwconfig.users[user_id]["revisionsbynamespace"]["*"])

    output += u"""</table>"""

    return output

def generatePagesTopUsersTable(page_id):
    if smwconfig.preferences["anonymous"]:
        return u"""<p>This is an anonymous analysis. This information will not be showed.</p>\n"""

    output = u"""<table>
    <tr><th>#</th><th>User</th><th>Edits</th></tr>"""

    top_users = {}
    for rev_id in smwconfig.pages[page_id]["revisions"]:
        rev_user = smwconfig.revisions[rev_id]["rev_user"]
        if top_users.has_key(rev_user):
            top_users[rev_user] += 1
        else:
            top_users[rev_user] = 1

    top_users_list = []
    for rev_user, edits in top_users.items():
        top_users_list.append([edits, rev_user])
    top_users_list.sort()
    top_users_list.reverse()

    c = 0
    for edits, rev_user in top_users_list:
        c += 1
        user_name = smwconfig.users[rev_user]["user_name"]
        page_title = smwconfig.pages[page_id]["page_title"]
        output += u"""<tr><td>%s</td><td><a href="../users/user_%s.html">%s</a></td><td><a href="%s/index.php?title=%s&amp;action=history">%s</a></td></tr>\n""" % (c, rev_user, user_name, smwconfig.preferences["siteUrl"], page_title, edits)
    output += u"""<tr><td></td><td>Total</td><td>%s</td></tr>""" % (len(smwconfig.pages[page_id]["revisions"]))

    output += u"""</table>"""

    return output

def generateUsersAnalysis():
    for user_id, user_props in smwconfig.users.items():
        user_name = user_props["user_name"]
        print u"Generating analysis to user: %s" % user_name
        generateUsersContentEvolution(user_id=user_id) #debe ir antes de rellenar el body, cuenta bytes, y antes de cortar por anonymous
        if smwconfig.preferences["anonymous"]:
            continue
        generateUsersTimeActivity(user_id=user_id)

        gallery = u""
        for img_name in smwconfig.users[user_id]["images"]:
            gallery += u"""<a href='%s/%s/Image:%s'><img src="%s" width="200px" alt="%s"/></a>&nbsp;&nbsp;&nbsp;""" % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], img_name, smwconfig.images[img_name]["img_url"], img_name)

        #avoiding zero division
        useredits = user_props["revisionsbynamespace"]["*"]
        usernm0edits = user_props["revisionsbynamespace"][0]
        usernm0editspercent = 0
        if useredits > 0:
            usernm0editspercent = usernm0edits/(useredits/100.0)
        userbytes = user_props["bytesbynamespace"]["*"]
        usernm0bytes = user_props["bytesbynamespace"][0]
        usernm0bytespercent = 0
        if userbytes > 0:
            usernm0bytespercent = usernm0bytes/(userbytes/100.0)

        body = u"""&lt;&lt; <a href="../../%s">Back</a>
        <table class="sections">
        <tr><th><b>Sections</b></th></tr>
        <tr><td><a href="#contentevolution">Content evolution</a></td></tr>
        <tr><td><a href="#activity">Activity</a></td></tr>
        <tr><td><a href="#mostedited">Most edited pages</a></td></tr>
        <tr><td><a href="#uploads">Uploads</a></td></tr>
        <tr><td><a href="#tagscloud">Tags cloud</a></td></tr>
        </table>
        <dl>
        <dt>User:</dt>
        <dd><a href='%s/%s/User:%s'>%s</a> (<a href="%s/%s/Special:Contributions/%s">contributions</a>)</dd>
        <dt>Edits:</dt>
        <dd>%d (In articles: %d, %.1f%%)</dd>
        <dt>Bytes added:</dt>
        <dd>%d (In articles: %d, %.1f%%)</dd>
        <dt>Files uploaded:</dt>
        <dd><a href="#uploads">%d</a></dd>
        </dl>
        <h2 id="contentevolution">Content evolution</h2>
        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_content_evolution.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_content_evolution.csv">CSV</a></td></tr>
        </table>
        <center>
        <img src="../../graphs/users/user_%s_content_evolution.png" alt="Content evolution" />
        </center>

        <h2 id="activity">Activity</h2>
        <center>
        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_hour_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_hour_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/users/user_%s_hour_activity.png" alt="Hour activity" /><br/>

        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_dayofweek_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_dayofweek_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/users/user_%s_dayofweek_activity.png" alt="Day of week activity" /><br/>

        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_month_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_month_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/users/user_%s_month_activity.png" alt="Month activity" />
        </center>
        <h2 id="mostedited">Most edited pages</h2>
        <center>
        %s
        </center>
        <h2 id="uploads">Uploads</h2>
        This user has uploaded %s files.<br/>
        <center>
        %s
        </center>
        <h2 id="tagscloud">Tags cloud</h2>
        <center>
        %s
        </center>
        &lt;&lt; <a href="../../%s">Back</a>
        """ % (smwconfig.preferences["indexFilename"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], user_name, user_name, smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], user_name, useredits, usernm0edits, usernm0editspercent, userbytes, usernm0bytes, usernm0bytespercent, len(user_props["images"]), user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, generateUsersMostEditedTable(user_id=user_id), len(smwconfig.users[user_id]["images"]), gallery, generateUsersCloud(user_id=user_id), smwconfig.preferences["indexFilename"])

        title = "%s: User:%s" % (smwconfig.preferences["siteName"], user_name)
        if not smwconfig.preferences["anonymous"]:
            smwhtml.printHTML(type="users", file="user_%s.html" % user_id, title=title, body=body)

def generateGeneralAnalysis():
    print "Generating general analysis"
    conn, cursor = smwdb.createConnCursor()

    cursor.execute("SELECT COUNT(user_id) AS count FROM %suser WHERE 1" % smwconfig.preferences["tablePrefix"])
    totalusers = int(cursor.fetchall()[0][0])

    #número de usuarios a partir de las revisiones y de la tabla de usuarios, len(user.items())
    cursor.execute("SELECT COUNT(rev_id) AS count FROM %srevision WHERE 1" % smwconfig.preferences["tablePrefix"])
    totaledits = int(cursor.fetchall()[0][0])

    #todo: con un inner join mejor?
    cursor.execute("SELECT COUNT(rev_id) AS count FROM %srevision WHERE rev_page IN (SELECT page_id FROM %spage WHERE page_namespace=0)" % (smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"]))
    totaleditsinarticles = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT COUNT(page_id) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"])
    totalpages = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT COUNT(*) AS count FROM %spage WHERE page_namespace=0 AND page_is_redirect=0" % smwconfig.preferences["tablePrefix"])
    totalarticles = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"])
    totalbytes = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE page_namespace=0 AND page_is_redirect=0" % smwconfig.preferences["tablePrefix"])
    totalbytesinarticles = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT SUM(page_counter) AS count FROM %spage WHERE 1" % smwconfig.preferences["tablePrefix"])
    totalvisits = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT SUM(page_counter) AS count FROM %spage WHERE page_namespace=0 AND page_is_redirect=0" % smwconfig.preferences["tablePrefix"])
    totalvisitsinarticles = int(cursor.fetchall()[0][0])

    cursor.execute("SELECT COUNT(*) AS count FROM %simage WHERE 1" % smwconfig.preferences["tablePrefix"])
    totalfiles = int(cursor.fetchall()[0][0])

    dateGenerated = datetime.datetime.now().isoformat()
    period = "%s &ndash; %s" % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())

    #avoiding zero division
    totalarticlespercent = 0
    if totalpages > 0:
        totalarticlespercent = totalarticles/(totalpages/100.0)
    totaleditsinarticlespercent = 0
    if totaledits > 0:
        totaleditsinarticlespercent = totaleditsinarticles/(totaledits/100.0)
    totalbytesinarticlespercent = 0
    if totalbytes > 0:
        totalbytesinarticlespercent = totalbytesinarticles/(totalbytes/100.0)
    totalvisitsinarticlespercent = 0
    if totalvisits > 0:
        totalvisitsinarticlespercent = totalvisitsinarticles/(totalvisits/100.0)

    body = u"""<table class="sections">
    <tr><th><b>Sections</b></th></tr>
    <tr><td><a href="#contentevolution">Content evolution</a></td></tr>
    <tr><td><a href="#activity">Activity</a></td></tr>
    <tr><td><a href="#users">Users</a></td></tr>
    <tr><td><a href="#pages">Pages</a></td></tr>
    <tr><td><a href="#categories">Categories</a></td></tr>
    <tr><td><a href="#tagscloud">Tags cloud</a></td></tr>
    </table>
    <dl>
    <dt>Site:</dt>
    <dd><a href='%s'>%s</a></dd>
    <dt>Report period:</dt>
    <dd>%s &ndash; %s</dd>
    <dt>Total pages:</dt>
    <dd><a href="#pages">%d</a> (Articles: %d, %.1f%%)</dd>
    <dt>Total edits:</dt>
    <dd>%d (In articles: %d, %.1f%%)</dd>
    <dt>Total bytes:</dt>
    <dd>%d (In articles: %d, %.1f%%)</dd>
    <dt>Total visits:</dt>
    <dd>%d (In articles: %d, %.1f%%)</dd>
    <dt>Total files:</dt>
    <dd><a href="%s/%s/Special:Imagelist">%d</a></dd>
    <dt>Users:</dt>
    <dd><a href="#users">%d</a></dd>
    <dt>Generated in:</dt>
    <dd>%s</dd>
    </dl>
    <h2 id="contentevolution">Content evolution</h2>

    <table class="downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/general/general_content_evolution.png">PNG</a></td></tr>
    <tr><td><a href="csv/general/general_content_evolution.csv">CSV</a></td></tr>
    </table>
    <center>
    <img src="graphs/general/general_content_evolution.png" alt="Content evolution" />
    </center>

    <h2 id="activity">Activity</h2>
    <center>
    <table class="downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/general/general_hour_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/general/general_hour_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/general/general_hour_activity.png" alt="Hour activity" /><br/>

    <table class="downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/general/general_dayofweek_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/general/general_dayofweek_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/general/general_dayofweek_activity.png" alt="Day of week activity" /><br/>

    <table class="downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/general/general_month_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/general/general_month_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/general/general_month_activity.png" alt="Month activity" />
    </center>

    <h2 id="users">Users</h2>
    <center>
    %s
    </center>
    <h2 id="pages">Pages</h2>
    <center>
    %s
    </center>
    <h2 id="categories">Categories</h2>
    <p>This analysis includes pages aggregated by categories.</p>
    <center>
    %s
    </center>
    <h2 id="tagscloud">Tags cloud</h2>
    <center>
    %s
    </center>
    """ % (smwconfig.preferences["siteUrl"], smwconfig.preferences["siteName"], smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat(), totalpages, totalarticles, totalarticlespercent, totaledits, totaleditsinarticles, totaleditsinarticlespercent, totalbytes, totalbytesinarticles, totalbytesinarticlespercent, totalvisits, totalvisitsinarticles, totalvisitsinarticlespercent, smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], totalfiles, totalusers, datetime.datetime.now().isoformat(), generateUsersTable(), generatePagesTable(), generateCategoriesTable(), generateGeneralCloud())

    generateGeneralContentEvolution()
    generateGeneralTimeActivity()

    smwhtml.printHTML(type="general", title=smwconfig.preferences["siteName"], body=body)

    smwdb.destroyConnCursor(conn, cursor)

def generatePagesAnalysis():
    for page_id, page_props in smwconfig.pages.items():
        page_title = page_props["page_title"]
        print u"Generating analysis to the page: %s" % page_title
        generatePagesContentEvolution(page_id=page_id)
        generatePagesTimeActivity(page_id=page_id)

        #avoiding zero division
        pageedits = page_props["edits"]
        pageanonedits = page_props["revisionsbyuserclass"]["anon"]
        pageanoneditspercent = 0
        if pageedits > 0:
            pageanoneditspercent = pageanonedits/(pageedits/100.0)
        pageregedits = page_props["revisionsbyuserclass"]["reg"]
        pageregeditspercent = 0
        if pageedits > 0:
            pageregeditspercent = pageregedits/(pageedits/100.0)

        body = u"""&lt;&lt; <a href="../../%s">Back</a>
        <table class="sections">
        <tr><th><b>Sections</b></th></tr>
        <tr><td><a href="#contentevolution">Content evolution</a></td></tr>
        <tr><td><a href="#activity">Activity</a></td></tr>
        <tr><td><a href="#topusers">Top users</a></td></tr>
        <tr><td><a href="#tagscloud">Tags cloud</a></td></tr>
        </table>
        <dl>
        <dt>Page:</dt>
        <dd><a href='%s/%s/%s'>%s</a> (<a href="%s/index.php?title=%s&amp;action=history">history</a>)</dd>
        <dt>Edits:</dt>
        <dd>%d (By anonymous users: %d, %.1f%%. By registered users: %d, %.1f%%)</dd>
        <dt>Bytes:</dt>
        <dd>%s</dd>
        </dl>

        <h2 id="contentevolution">Content evolution</h2>
        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_content_evolution.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_content_evolution.csv">CSV</a></td></tr>
        </table>
        <center>
        <img src="../../graphs/pages/page_%s_content_evolution.png" alt="Content evolution" />
        </center>

        <h2 id="activity">Activity</h2>
        <center>
        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_hour_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_hour_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/pages/page_%s_hour_activity.png" alt="Hour activity" /><br/>

        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_dayofweek_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_dayofweek_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/pages/page_%s_dayofweek_activity.png" alt="Day of week activity" /><br/>

        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_month_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_month_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/pages/page_%s_month_activity.png" alt="Month activity" />
        </center>
        <h2 id="topusers">Top users</h2>
        <center>
        %s
        </center>
        <h2 id="tagscloud">Tags cloud</h2>
        <center>
        %s
        </center>
        &lt;&lt; <a href="../../%s">Back</a>
        """ % (smwconfig.preferences["indexFilename"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], page_title, page_title, smwconfig.preferences["siteUrl"], page_title, pageedits, pageanonedits, pageanoneditspercent, pageregedits, pageregeditspercent, page_props["page_len"], page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, generatePagesTopUsersTable(page_id=page_id), generatePagesCloud(page_id=page_id), smwconfig.preferences["indexFilename"])

        title = "%s: %s" % (smwconfig.preferences["siteName"], page_title)
        smwhtml.printHTML(type="pages", file="page_%s.html" % page_id, title=title, body=body)

def generateCategoriesAnalysis():
    for category_title, page_ids in smwconfig.categories.items():
        category_id = smwget.pagetitle2pageid(page_title=category_title, page_namespace=14)
        if not category_id:
            #necesitamos un page_id para la categoría, para los nombres de los ficheros, no nos lo vamos a inventar
            #así que si no existe, no generamos análisis para esa categoría
            print "Some pages are categorised into %s but there is no page for that category" % (category_title)
            continue
        print u"Generating analysis to the category: %s" % category_title
        generateCategoriesContentEvolution(category_id=category_id, page_ids=page_ids)
        generateCategoriesTimeActivity(page_id=category_id)

        #avoiding zero division
        catedits = 0
        for page_id, page_props in smwconfig.pages.items():
            if page_id in page_ids:
                catedits += page_props["edits"]

        catanonedits = 0
        for page_id, page_props in smwconfig.pages.items():
            if page_id in page_ids:
                catanonedits += page_props["revisionsbyuserclass"]["anon"]
        catanoneditspercent = 0
        if catedits > 0:
            catanoneditspercent = catanonedits/(catedits/100.0)

        catregedits = 0
        for page_id, page_props in smwconfig.pages.items():
            if page_id in page_ids:
                catregedits += page_props["revisionsbyuserclass"]["reg"]
        catregeditspercent = 0
        if catedits > 0:
            catregeditspercent = catregedits/(catedits/100.0)

        body = u"""&lt;&lt; <a href="../../%s">Back</a>
        <table class="sections">
        <tr><th><b>Sections</b></th></tr>
        <tr><td><a href="#contentevolution">Content evolution</a></td></tr>
        <tr><td><a href="#activity">Activity</a></td></tr>
        <tr><td><a href="#topusers">Top users</a></td></tr>
        <tr><td><a href="#topusers">Top pages</a></td></tr>
        <tr><td><a href="#tagscloud">Tags cloud</a></td></tr>
        </table>
        <dl>
        <dt>Category:</dt>
        <dd><a href='%s/%s/Category:%s'>%s</a> (<a href="%s/index.php?title=Category:%s&amp;action=history">history</a>)</dd>
        <dt>Edits to pages in this category:</dt>
        <dd>%d (By anonymous users: %d, %.1f%%. By registered users: %d, %.1f%%)</dd>
        <dt>Pages:</dt>
        <dd>%s</dd>
        </dl>
        <h2 id="contentevolution">Content evolution</h2>
        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_content_evolution.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_content_evolution.csv">CSV</a></td></tr>
        </table>
        <center>
        <img src="../../graphs/categories/category_%d_content_evolution.png" alt="Content evolution" />
        </center>

        <h2 id="activity">Activity</h2>
        <center>
        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_hour_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_hour_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/categories/category_%d_hour_activity.png" alt="Hour activity" /><br/>

        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_dayofweek_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_dayofweek_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/categories/category_%d_dayofweek_activity.png" alt="Day of week activity" /><br/>

        <table class="downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_month_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_month_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/categories/category_%d_month_activity.png" alt="Month activity" />
        </center>
        <h2 id="topusers">Top users</h2>
        <center>
        %s
        </center>
        <h2 id="topusers">Top pages</h2>
        <center>
        %s
        </center>
        <h2 id="tagscloud">Tags cloud</h2>
        <center>
        %s
        </center>
        &lt;&lt; <a href="../../%s">Back</a>
        """ % (smwconfig.preferences["indexFilename"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], category_title, category_title, smwconfig.preferences["siteUrl"], category_title, catedits, catanonedits, catanoneditspercent, catregedits, catregeditspercent, len(smwconfig.categories[category_title]), category_id, category_id, category_id, category_id, category_id, category_id, category_id, category_id, category_id, category_id, category_id, category_id, "", "", generateCategoriesCloud(category_id=category_id, page_ids=page_ids), smwconfig.preferences["indexFilename"]) #crear topuserstable para las categorias y fusionarla con generatePagesTopUsersTable(page_id=page_id) del las páginas y el global (así ya todas muestran los incrementos en bytes y porcentajes, además de la ediciones), lo mismo para el top de páginas más editadas

        title = "%s: Pages in category %s" % (smwconfig.preferences["siteName"], category_title)
        smwhtml.printHTML(type="categories", file="category_%s.html" % category_id, title=title, body=body)

