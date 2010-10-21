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
    generateGlobalAnalysis()
    generateUsersAnalysis()
    generatePagesAnalysis()
    generateCategoriesAnalysis()

def generadorColumnaFechas(startDate, delta=datetime.timedelta(days=1)):
    # Generamos una columna virtual con fechas a partir de una fecha
    # determinada, con un salto determinado entre elementos (por omision,
    # un dia)
    currentDate = startDate
    while True:
        yield currentDate
        currentDate += delta

def generateWorkDistribution(type, fileprefix, page_props=None, category_props=None):
    assert type == "global" or (type == "pages" and page_props) or (type == "categories" and category_props)

    usersSortedByEdittime = []
    if type == "pages":
        usersSortedByEdittime = smwget.getUsersSortedByEdittimeInPage(page_props=page_props)
    elif type == "categories":
        usersSortedByEdittime = smwget.getUsersSortedByEdittimeInCategory(category_props=category_props)

    fecha = smwconfig.preferences["startDate"]
    fechaincremento = datetime.timedelta(days=1)
    usersCount = {}
    usersCountPercent = {}
    usersCountPercent2 = {}
    #initialize dics
    for firstrevisiondate, user_text_ in usersSortedByEdittime: #no importa que el dic no guarde el orden, luego en el bucle usamos la lista ordenada de nuevo
        usersCount[user_text_] = []
        usersCountPercent[user_text_] = []
        usersCountPercent2[user_text_] = []
    days = 0
    while fecha < smwconfig.preferences["endDate"]: #fix es < o <= ? (en contentevol pasa lo mismo)
        usersCountThisDay = {}
        #initialize dic
        for firstrevisiondate, user_text_ in usersSortedByEdittime:
            if days == 0:
                usersCountThisDay[user_text_] = 0 #first day
            else:
                usersCountThisDay[user_text_] = usersCount[user_text_][days-1] #acum previous days

        for rev_id, rev_props in smwconfig.revisions.items():
            if type == "pages":
                if rev_props["rev_page"] != page_props["page_id"]:
                    continue #nos la saltamos, no es de esta página
            elif type == "categories":
                if rev_props["rev_page"] not in category_props["pages"]:
                    continue #nos la saltamos, esta revisión no es de una página de esta categoría

            if rev_props["rev_timestamp"] < fecha and rev_props["rev_timestamp"] >= fecha - fechaincremento: # 00:00:00 < fecha < 23:59:59
                rev_page = rev_props["rev_page"]
                if type == "pages" or type == "categories":
                    if rev_props["len_diff"] > 0:
                        usersCountThisDay[rev_props["rev_user_text_"]] += rev_props["len_diff"]
        #ahora, según el orden determinado por la fecha de participación,
        for firstrevisiondate, user_text_ in usersSortedByEdittime:
            usersCount[user_text_].append(usersCountThisDay[user_text_])

        fecha += fechaincremento
        days += 1
    
    #the percent for every day for every user, respects to the total bytes acumulatted until that day
    for i in range(days):
        subtotal = sum([count[i] for user_text_, count in usersCount.items()])
        [usersCountPercent[user_text_].append(subtotal and count[i]/(subtotal/100.0) or 0) for user_text_, count in usersCount.items()]
    
    #the accumulated percent for every user using the order of the list by datetime
    for i in range(days):
        j = 0
        for firstrevisiondate, user_text_ in usersSortedByEdittime:
            usersCountPercent2[user_text_].append(sum([v[i] for k, v in usersCountPercent.items() if k in [v2 for k2, v2 in usersSortedByEdittime[:j+1]]]))
            j += 1

    rows = []
    headers = []
    #as accumulated is sorted by first edit datetime, we use it here too
    for firstrevisiondate, user_text_ in usersSortedByEdittime:
        #print user_text_, usersCount[user_text_]
        #print user_text_, usersCountPercent[user_text_]
        #print user_text_, usersCountPercent2[user_text_]
        rows.append(usersCountPercent2[user_text_]+[0]) #adding a last point with zero value to make filledcurve return to x axis base
        headers.append(user_text_)
    #necessary to print the layers in the correct order (first, the 100% layer, and descending ...)
    headers.reverse()
    rows.reverse()

    title = ""
    if type == "pages":
        title = "Accumulative work distribution in %s" % page_props["full_page_title"]
    elif type == "categories":
        title = "Accumulative work distribution in category %s" % category_props["category_title"]

    smwplot.printGraphWorkDistribution(type=type, fileprefix=fileprefix,
                                   title=title, headers=headers,
                                   rows=rows)

def generatePagesWorkDistribution(page_props=None):
    assert page_props
    generateWorkDistribution(type="pages", fileprefix="page_%d" % page_props["page_id"], page_props=page_props)

def generateCategoriesWorkDistribution(category_props=None):
    assert category_props
    generateWorkDistribution(type="categories", fileprefix="category_%d" % category_props["category_id"], category_props=category_props)

def generateTimeActivity(timesplit, type, fileprefix, conds, headers, user_props=None, page_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)
    results = {}

    conn, cursor = smwdb.createConnCursor()
    for cond in conds:
        #todo: en vez de sql-query, usar el dic revisions y datetime.datetime.dow, etc
        cursor.execute("SELECT %s(rev_timestamp) AS time, COUNT(rev_id) AS count FROM %srevision, %spage WHERE rev_page=page_id and rev_timestamp>='%s' and rev_timestamp<='%s' AND %s GROUP BY time ORDER BY time" % (timesplit, smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], smwconfig.preferences["startDateMW"], smwconfig.preferences["endDateMW"], cond))
        result = cursor.fetchall()
        results[cond] = {}
        for timestamp, edits in result:
            if timesplit in ["dayofweek", "month"]:
                timestamp = timestamp - 1
            results[cond][str(timestamp)] = str(edits)
    smwdb.destroyConnCursor(conn, cursor)

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
    if type == "global":
        if timesplit == "hour":
            title = 'Hour activity in %s' % smwconfig.preferences["siteName"]
        elif timesplit == "dayofweek":
            title = 'Day of week activity in %s' % smwconfig.preferences["siteName"]
        elif timesplit == "month":
            title = 'Month activity in %s' % smwconfig.preferences["siteName"]
    elif type == "users":
        if timesplit == "hour":
            title = "Hour activity by %s" % user_props["user_name"]
        elif timesplit == "dayofweek":
            title = "Day of week activity by %s" % user_props["user_name"]
        elif timesplit == "month":
            title = "Month activity by %s" % user_props["user_name"]
    elif type == "pages":
        if timesplit == "hour":
            title = "Hour activity in %s" % page_props["full_page_title"]
        elif timesplit == "dayofweek":
            title = "Day of week activity in %s" % page_props["full_page_title"]
        elif timesplit == "month":
            title = "Month activity in %s" % page_props["full_page_title"]
    elif type == "categories":
        if timesplit == "hour":
            title = "Hour activity in category %s" % category_props["category_title"]
        elif timesplit == "dayofweek":
            title = "Day of week activity in category %s" % category_props["category_title"]
        elif timesplit == "month":
            title = "Month activity in category %s" % category_props["category_title"]

    # Print rows
    smwcsv.printCSV(type=type, subtype="activity", fileprefix=fileprefix,
             headers=headers, rows=rows)
    smwplot.printGraphTimeActivity(type=type, fileprefix=fileprefix, title=title,
                           headers=headers, rows=rows)

def generateGlobalTimeActivity():
    conds = ["1", "page_namespace=0", "page_namespace=1"] # artículo o todas
    headers = ["Edits (all pages)", "Edits (only articles)", "Edits (only articles talks)"]
    generateTimeActivity(timesplit="hour", type="global", fileprefix="global", conds=conds, headers=headers)
    generateTimeActivity(timesplit="dayofweek", type="global", fileprefix="global", conds=conds, headers=headers)
    generateTimeActivity(timesplit="month", type="global", fileprefix="global", conds=conds, headers=headers)

def generatePagesTimeActivity(page_props=None):
    assert page_props
    conds = ["1 and rev_page=%d" % page_props["page_id"], "rev_user=0 and rev_page=%d" % page_props["page_id"], "rev_user!=0 and rev_page=%d" % page_props["page_id"]] #todas, anónimas o registrados
    headers = ["Edits in %s (all users)" % page_props["full_page_title"], "Edits in %s (only anonymous users)" % page_props["full_page_title"], "Edits in %s (only registered users)" % page_props["full_page_title"]]
    generateTimeActivity(timesplit="hour", type="pages", fileprefix="page_%d" % page_props["page_id"], conds=conds, headers=headers, page_props=page_props)
    generateTimeActivity(timesplit="dayofweek", type="pages", fileprefix="page_%d" % page_props["page_id"], conds=conds, headers=headers, page_props=page_props)
    generateTimeActivity(timesplit="month", type="pages", fileprefix="page_%d" % page_props["page_id"], conds=conds, headers=headers, page_props=page_props)

def generateCategoriesTimeActivity(category_props=None):
    assert category_props
    conds2 = ["1", "rev_user=0", "rev_user!=0"] #todas, anónimas o registrados
    conds = []
    for cond in conds2:
        conds.append("%s and rev_page in (select cl_from from categorylinks where cl_to='%s')" % (cond, category_props["category_title_"].encode(smwconfig.preferences['codification']))) #fix cuidado con nombres de categorías con '
    headers = ["Edits in category %s (all users)" % category_props["category_title"], "Edits in category %s (only anonymous users)" % category_props["category_title"], "Edits in category %s (only registered users)" % category_props["category_title"]]
    generateTimeActivity(timesplit="hour", type="categories", fileprefix="category_%d" % category_props["category_id"], conds=conds, headers=headers, category_props=category_props)
    generateTimeActivity(timesplit="dayofweek", type="categories", fileprefix="category_%d" % category_props["category_id"], conds=conds, headers=headers, category_props=category_props)
    generateTimeActivity(timesplit="month", type="categories", fileprefix="category_%d" % category_props["category_id"], conds=conds, headers=headers, category_props=category_props)

def generateUsersTimeActivity(user_props=None):
    assert user_props
    conds = ["rev_user_text='%s'" % user_props["user_name"].encode(smwconfig.preferences['codification']), "page_namespace=0 and rev_user_text='%s'" % user_props["user_name"].encode(smwconfig.preferences['codification']), "page_namespace=1 and rev_user_text='%s'" % user_props["user_name"].encode(smwconfig.preferences['codification'])] # artículo o todas, #todo añadir escape() para comillas?
    headers = ["Edits by %s (all pages)" % user_props["user_name"], "Edits by %s (only articles)" % user_props["user_name"], "Edits by %s (only articles talks)" % user_props["user_name"]]
    filesubfix = user_props["user_id"]
    if filesubfix == 0:
        filesubfix = user_props["user_name_"]
    generateTimeActivity(timesplit="hour", type="users", fileprefix="user_%s" % filesubfix, conds=conds, headers=headers, user_props=user_props)
    generateTimeActivity(timesplit="dayofweek", type="users", fileprefix="user_%s" % filesubfix, conds=conds, headers=headers, user_props=user_props)
    generateTimeActivity(timesplit="month", type="users", fileprefix="user_%s" % filesubfix, conds=conds, headers=headers, user_props=user_props)

def generateCloud(type=None, user_props=None, page_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)

    cloud = {}
    for rev_id, rev_props in smwconfig.revisions.items():
        if type == "users" and rev_props["rev_user_text_"] != user_props["user_name_"]:
            continue
        elif type == "pages" and rev_props["rev_page"] != page_props["page_id"]:
            continue
        elif type == "categories" and rev_props["rev_page"] not in category_props["pages"]: #no ponemos and page_ids, puesto que puede ser una categoría vacía
            continue

        comment = rev_props["rev_comment"]
        comment = unicode(rev_props["rev_comment"].encode(smwconfig.preferences["codification"]).lower().strip(), smwconfig.preferences["codification"]) #ugly line neccesary to avoid text being bad codify by use lower()
        comment = re.sub("[\[\]\=\,\{\}\|\:\;\"\'\?\¿\/\*\(\)\<\>\+\.\-\#\_\&]", " ", comment) #no commas, csv
        comment = re.sub("  +", " ", comment)
        tags = comment.split(' ')
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

    output = ''
    cloudListShuffle = cloudList[:limit]
    random.shuffle(cloudListShuffle)
    for times, tag in cloudListShuffle:
        if maxTimes - minTimes > 0:
            fontsize = 100 + ((times - minTimes) * (maxSize - minSize)) / (maxTimes - minTimes)
        else:
            fontsize = 100 + (maxSize - minSize ) / 2
        output += '<span style="font-size: %s%%">%s</span> &nbsp;&nbsp;&nbsp;' % (fontsize, tag)

    if not output:
        output += 'There is no comments in edits.'

    return output

def generateTableByNamespace(type=None, htmlid=None, fun=None, user_props=None, page_props=None, category_props=None):
    assert (type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)) and htmlid and fun
    output = '[<a href="javascript:showHide(\'%s\')">Show/Hide</a>]\n<div id="%s" style="display: none;"><table class="prettytable">' % (htmlid, htmlid)
    namespaces = smwconfig.namespaces.items()
    namespaces.sort()
    for nmnum, nmname in namespaces:
        if type == "global":
            output += '<tr><td><b>%s</b></td><td>%d</td></tr>' % (nmname, fun(namespace=nmnum))
        elif type == "users":
            output += '<tr><td><b>%s</b></td><td>%d</td></tr>' % (nmname, fun(user_props=user_props, namespace=nmnum))
        elif type == "pages":
            pass #todo
        elif type == "categories":
            pass #todo
    output += '</table></div>'
    return output

def generateSummary(type, user_props=None, page_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)
    output = '<table class="prettytable summary">'

    if type == "global":
        output += '<tr><td><b>Site:</b></td><td><a href="%s">%s</a> (<a href="%s/%s/Special:Recentchanges">recent changes</a>)</td></tr>\n' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["siteName"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td></tr>\n' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total users:</b></td><td><a href="#topusers">%d</a></td></tr>\n' % (smwget.getTotalUsers())
        output += '<tr><td><b>Total pages:</b></td><td><a href="#toppages">%d</a> %s</td></tr>\n' % (smwget.getTotalPages(), generateTableByNamespace(type="global", htmlid='global-pages', fun=smwget.getTotalPagesByNamespace))
        output += '<tr><td><b>Total edits:</b></td><td>%d %s</td></tr>\n' % (smwget.getTotalRevisions(), generateTableByNamespace(type="global", htmlid='global-edits', fun=smwget.getTotalRevisionsByNamespace))
        output += '<tr><td><b>Total bytes:</b></td><td>%d %s</td></tr>\n' % (smwget.getTotalBytes(), generateTableByNamespace(type="global", htmlid='global-bytes', fun=smwget.getTotalBytesByNamespace))
        output += '<tr><td><b>Total files:</b></td><td>%d</td></tr>\n' % (smwget.getTotalImages())
        output += '<tr><td><b>Total visits:</b></td><td>%d %s</td></tr>\n' % (smwget.getTotalVisits(), generateTableByNamespace(type="global", htmlid='global-visits', fun=smwget.getTotalVisitsByNamespace))
    elif type == "users":
        output += '<tr><td><b>User:</b></td><td><a href="%s/%s/User:%s">%s</a> (<a href="%s/%s/Special:Contributions/%s">contributions</a>)</td></tr>\n' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], user_props["user_name_"], user_props["user_name"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], user_props["user_name_"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td></tr>\n' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total pages edited:</b></td><td><a href="#toppages">%d</a> %s</td></tr>\n' % (smwget.getTotalPagesByUser(user_text_=user_props["user_name_"]), generateTableByNamespace(type="users", htmlid='user-pages', fun=smwget.getTotalPagesByUserByNamespace, user_props=user_props))#fix: renombrar a PagesEdited y hacer PagesCreated?
        output += '<tr><td><b>Total edits:</b></td><td>%d (<a href="../../%s#topusers">#%d</a>) %s</td></tr>\n' % (smwget.getTotalRevisionsByUser(user_text_=user_props["user_name_"]), smwconfig.preferences["indexFilename"], [v for k, v in smwget.getUsersSortedByTotalRevisions()].index(user_props["user_name_"]) + 1, generateTableByNamespace(type="users", htmlid='user-edits', fun=smwget.getTotalRevisionsByUserInNamespace, user_props=user_props))
        output += '<tr><td><b>Total bytes:</b></td><td>%d (<a href="../../%s#topusers">#%d</a>) %s</td></tr>\n' % (smwget.getTotalBytesByUser(user_text_=user_props["user_name_"]), smwconfig.preferences["indexFilename"], [v for k, v in smwget.getUsersSortedByTotalBytes()].index(user_props["user_name_"]) + 1, generateTableByNamespace(type="users", htmlid='user-bytes', fun=smwget.getTotalBytesByUserInNamespace, user_props=user_props))
        output += '<tr><td><b>Total files:</b></td><td><a href="#uploads">%d</a> (<a href="../../%s#topusers">#%d</a>)</td></tr>\n' % (smwget.getTotalImagesByUser(user_text_=user_props["user_name_"]), smwconfig.preferences["indexFilename"], [v for k, v in smwget.getUsersSortedByTotalImages()].index(user_props["user_name_"]) + 1)
    elif type == "pages":
        pagelink = '%s/%s/%s' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], page_props["full_page_title_"])
        if page_props["page_is_redirect"]:
            pagelink = '%s/index.php?title=%s&redirect=no' % (smwconfig.preferences["siteUrl"], page_props["full_page_title_"])
        output += '<tr><td><b>Page:</b></td><td><a href="%s">%s</a> (<a href="%s/index.php?title=%s&amp;action=history">history</a>)</td></tr>\n' % (pagelink, page_props["full_page_title"], smwconfig.preferences["siteUrl"], page_props["full_page_title_"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td></tr>\n' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Namespace:</b></td><td>%s</td></tr>\n' % (smwconfig.namespaces[page_props["page_namespace"]])
        output += '<tr><td><b>Page is redirect:</b></td><td>%s</td></tr>\n' % (page_props["page_is_redirect"] and 'Yes' or 'No')
        output += '<tr><td><b>Total users:</b></td><td><a href="#topusers">%d</a></td></tr>\n' % (smwget.getTotalUsersByPage(page_id=page_props["page_id"]))
        output += '<tr><td><b>Total edits:</b></td><td>%d</td></tr>\n' % (smwget.getTotalRevisionsByPage(page_id=page_props["page_id"]))
        output += '<tr><td><b>Total bytes:</b></td><td>%d</td></tr>\n' % (page_props["page_len"])
        output += '<tr><td><b>Total visits:</b></td><td>%d</td></tr>\n' % (page_props["page_counter"])
    elif type == "categories":
        output += '<tr><td><b>Category:</b></td><td><a href="%s/%s/Category:%s">%s</a> (<a href="%s/index.php/Special:Relatedchanges/Category:%s">related changes</a>)</td></tr>\n' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], category_props["category_title_"], category_props["category_title"], smwconfig.preferences["siteUrl"], category_props["category_title_"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td></tr>\n' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total pages included:</b></td><td><a href="#toppages">%d</a></td></tr>\n' % (len(category_props["pages"]))
        output += '<tr><td><b>Total users:</b></td><td><a href="#topusers">%d</a></td></tr>\n' % (smwget.getTotalUsersByCategory(category_props=category_props))
        output += '<tr><td><b>Total edits:</b></td><td>%d</td></tr>\n' % (smwget.getTotalRevisionsByCategory(category_props=category_props))
        output += '<tr><td><b>Total bytes:</b></td><td>%d</td></tr>\n' % (smwget.getTotalBytesByCategory(category_props=category_props))

    output += '<tr><td><b>Generated in:</b></td><td>%s</td></tr>\n' % (datetime.datetime.now().isoformat())

    """
    ediciones menores, in articles
    ediciones anónimas (no aplica a users), in articles
    primera edición
    edición más reciente
    tiempo entre ediciones
    promedio ediciones por mes
    promedio ediciones por año
    número ediciones último día
    última semana
    último mes
    último año
    número de usuarios (no aplica a users)
    ediciones promedio por usuario (no aplica a users)
    pareto número de ediciones hechas por el top 10% de usuarios (no aplica a users)
    """

    output += "</table>"

    return output

def generateContentEvolution(type, user_props=None, page_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)

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
            if type == "global":
                pass #nos interesan todas
            elif type == "users":
                if rev_props["rev_user_text_"] != user_props["user_name_"]:
                    continue #nos la saltamos, no es de este usuario
            elif type == "pages":
                if rev_props["rev_page"] != page_props["page_id"]:
                    continue #nos la saltamos, no es de esta página
            elif type == "categories":
                if rev_props["rev_page"] not in category_props["pages"]:
                    continue #nos la saltamos, esta revisión no es de una página de esta categoría

            if rev_props["rev_timestamp"] < fecha and rev_props["rev_timestamp"] >= fecha - fechaincremento: # 00:00:00 < fecha < 23:59:59
                rev_page = rev_props["rev_page"]
                if type == "global":
                    #más adelante quizás convenga poner la evolución del contenido según anónimos y registrados, para el caso global
                    #evolución de todas las páginas
                    count1 += rev_props["len_diff"]
                    if smwconfig.pages[rev_page]["page_namespace"] == 0:
                        count2 += rev_props["len_diff"]
                    if smwconfig.pages[rev_page]["page_namespace"] == 1:
                        count3 += rev_props["len_diff"]
                elif type == "pages" or type == "categories":
                    count1 += rev_props["len_diff"]
                    if rev_props["rev_user"] == 0: #anon
                        count2 += rev_props["len_diff"]
                    else:
                        count3 += rev_props["len_diff"]
                elif type == "users":
                    if rev_props["len_diff"] <= 0:
                        #conv: solo contamos las diferencias positivas para los usuarios, de momento
                        #para el global y las páginas, sí hay retrocesos
                        continue
                    count1 += rev_props["len_diff"]
                    if smwconfig.pages[rev_page]["page_namespace"] == 0:
                        count2 += rev_props["len_diff"]
                    if smwconfig.pages[rev_page]["page_namespace"] == 1:
                        count3 += rev_props["len_diff"]
                    #evolución de todas las páginas

        graph1.append(count1)
        graph2.append(count2)
        graph3.append(count3)

        fecha += fechaincremento

    title = ''
    fileprefix = ''
    owner = ''
    if type == "global":
        title = 'Content evolution in %s' % smwconfig.preferences["siteName"]
        fileprefix = "global"
        owner = smwconfig.preferences["siteName"]
    elif type == "users":
        title = 'Content evolution by %s' % user_props["user_name"]
        if user_props["user_id"] == 0:
            fileprefix = "user_%s" % user_props["user_name_"]
        else:
            fileprefix = "user_%s" % user_props["user_id"]
        owner = user_props["user_name"]
    elif type == "pages":
        title = 'Content evolution in %s' % (page_props["full_page_title"])
        fileprefix = "page_%s" % page_props["page_id"]
        owner = page_props["full_page_title"]
    elif type == "categories":
        title = 'Content evolution for pages in %s' % category_props["category_title"]
        fileprefix = "category_%s" % category_props["category_id"]
        owner = category_props["category_title"]

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

def generateUsersTable(type=None, page_props=None, category_props=None):
    assert type == "global" or (type == "pages" and page_props) or (type == "categories" and category_props)
    assert type != "users" #no necesaria esta tabla para usuarios

    if type == "pages" and smwconfig.preferences["anonymous"]:
        return '<p>This is an anonymous analysis. This information will not be showed.</p>\n'

    output = ''
    #legend
    output += smwhtml.getLegend()

    #table
    output += '<table class="prettytable"><tr>'
    output += '<th>#</th><th>User</th><th>Edits</th><th>%</th>'
    if type != "pages": # no tiene sentido dentro de páginas
        output += '<th>Edits in articles</th><th>%</th>'
    output += '<th>Bytes</th><th>%</th>'
    if type != "pages":
        output += '<th>Bytes in articles</th><th>%</th>'
    if type == "global":
        output += '<th>Uploads</th><th>%</th>'
    output += '</tr>'

    usersSorted = []
    totalrevisions = 0
    totalrevisionsinarticles = 0
    totalbytes = 0
    totalbytesinarticles = 0
    totaluploads = 0
    if type == "global":
        usersSorted = smwget.getUsersSortedByTotalRevisions()
        totalrevisions = smwget.getTotalRevisions()
        totalrevisionsinarticles = smwget.getTotalRevisionsByNamespace(namespace=0)
        totalbytes = smwget.getTotalBytes()
        totalbytesinarticles = smwget.getTotalBytesByNamespace(namespace=0)
        totaluploads = smwget.getTotalImages()
    elif type == "pages":
        usersSorted = smwget.getUsersSortedByTotalRevisionsInPage(page_id=page_props["page_id"])
        totalrevisions = smwget.getTotalRevisionsByPage(page_id=page_props["page_id"])
        totalbytes = page_props["page_len"]
    elif type == "categories":
        usersSorted = smwget.getUsersSortedByTotalRevisionsInCategory(category_props=category_props)
        totalrevisions = smwget.getTotalRevisionsByCategory(category_props=category_props)
        totalrevisionsinarticles = smwget.getTotalRevisionsByCategoryByNamespace(category_props=category_props, namespace=0)
        totalbytes = smwget.getTotalBytesByCategory(category_props=category_props)
        totalbytesinarticles = smwget.getTotalBytesByCategoryByNamespace(category_props=category_props, namespace=0)

    c = 1
    acumrevisions = 0
    acumrevisionsinarticles = 0
    acumbytes = 0
    acumbytesinarticles = 0
    acumuploads = 0
    for numrevisions, user_text_ in usersSorted:
        if type != "global" and numrevisions == 0:
            continue

        filesubfix = smwconfig.users[user_text_]["user_id"]
        if filesubfix == 0: #ip
            filesubfix = user_text_

        #start row
        output += '<tr><td>%d</td>' % (c)
        output += '<td><a href="%s/users/user_%s.html">%s</a></td>' % (type == "global" and 'html' or '..', filesubfix, smwconfig.users[user_text_]["user_name"])

        #revisions
        maxi = 0
        if type == "global":
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisions()] + [0]))
        elif type == "pages":
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisionsInPage(page_id=page_props["page_id"])] + [0]))
        elif type == "categories":
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisionsInCategory(category_props=category_props)] + [0]))
        acumrevisions += numrevisions
        percent = totalrevisions > 0 and numrevisions/(totalrevisions/100.0) or 0
        color = maxi and numrevisions/(maxi/smwconfig.preferences["numColors"]) or 0
        output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numrevisions, color, percent)

        #revisions in articles
        numrevisionsinarticles = 0
        maxi = 0
        if type == "global":
            numrevisionsinarticles = smwget.getTotalRevisionsByUserInNamespace(user_props=smwconfig.users[user_text_], namespace=0)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisionsInNamespace(namespace=0)] + [0]))
        elif type == "pages":
            pass #no required
        elif type == "categories":
            numrevisionsinarticles = smwget.getTotalRevisionsByUserByCategoryInNamespace(user_text_=user_text_, category_props=category_props, namespace=0)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisionsByCategoryInNamespace(category_props=category_props, namespace=0)] + [0]))
        if type != "pages":
            acumrevisionsinarticles += numrevisionsinarticles
            percent = totalrevisionsinarticles > 0 and numrevisionsinarticles/(totalrevisionsinarticles/100.0) or 0
            color = maxi and numrevisionsinarticles/(maxi/smwconfig.preferences["numColors"]) or 0
            output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numrevisionsinarticles, color, percent)

        #bytes
        numbytes = 0
        maxi = 0
        if type == "global":
            numbytes = smwget.getTotalBytesByUser(user_text_=user_text_)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytes()] + [0]))
        elif type == "pages":
            numbytes = smwget.getTotalBytesByUserInPage(user_text_=user_text_, page_id=page_props["page_id"])
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytesInPage(page_id=page_props["page_id"])] + [0]))
        elif type == "categories":
            numbytes = smwget.getTotalBytesByUserInCategory(user_text_=user_text_, category_props=category_props)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytesInCategory(category_props=category_props)] + [0]))
        acumbytes += numbytes
        percent = totalbytes > 0 and numbytes/(totalbytes/100.0) or 0
        color = maxi and numbytes/(maxi/smwconfig.preferences["numColors"]) or 0
        output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numbytes, color, percent)

        #bytes in articles
        numbytesinarticles = 0
        maxi = 0
        if type == "global":
            numbytesinarticles = smwget.getTotalBytesByUserInNamespace(user_props=smwconfig.users[user_text_], namespace=0)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytesInNamespace(namespace=0)] + [0]))
        elif type == "pages":
            pass #no required
        elif type == "categories":
            numbytesinarticles = smwget.getTotalBytesByUserByCategoryInNamespace(user_text_=user_text_, category_props=category_props, namespace=0)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytesByCategoryInNamespace(category_props=category_props, namespace=0)] + [0]))
        if type != "pages":
            acumbytesinarticles += numbytesinarticles
            percent = totalbytesinarticles > 0 and numbytesinarticles/(totalbytesinarticles/100.0) or 0
            color = maxi and numbytesinarticles/(maxi/smwconfig.preferences["numColors"]) or 0
            output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numbytesinarticles, color, percent)

        #uploads
        numuploads = 0
        maxi = 0
        if type == "global":
            numuploads = smwget.getTotalImagesByUser(user_text_=user_text_)
            acumuploads += numuploads
            percent = totaluploads > 0 and numuploads/(totaluploads/100.0) or 0
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalImages()] + [0]))
            color = maxi and numuploads/(maxi/smwconfig.preferences["numColors"]) or 0
            output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numuploads, color, percent)

        #end row
        output += '</tr>\n'
        c += 1

    #total row
    output += '<tr><td colspan="2">Total</td>'
    output += '<td>%d</td><td>%.1f%%</td>' % (acumrevisions, totalrevisions and acumrevisions/(totalrevisions/100.0) or 0)
    if type != "pages":
        output += '<td>%d</td><td>%.1f%%</td>' % (acumrevisionsinarticles, totalrevisionsinarticles and acumrevisionsinarticles/(totalrevisionsinarticles/100.0) or 0)
    output += '<td>%d<sup>[<a href="#note1">1</a>]</sup></td><td>%.1f%%<sup>[<a href="#note1">1</a>]</sup></td>' % (acumbytes, totalbytes and acumbytes/(totalbytes/100.0) or 0)
    if type != "pages":
        output += '<td>%d<sup>[<a href="#note1">1</a>]</sup></td><td>%.1f%%<sup>[<a href="#note1">1</a>]</sup></td>' % (acumbytesinarticles, totalbytesinarticles and acumbytesinarticles/(totalbytesinarticles/100.0) or 0)
    if type == "global":
        output += '<td>%d</td><td>%.1f%%</td>' % (acumuploads, totaluploads and acumuploads/(totaluploads/100.0) or 0)
    output += '</tr>'
    output += '</table>'

    #notes
    note1in = ''
    if type == "global":
        note1in = 'in the wiki'
    elif type == "pages":
        note1in = 'in the page'
    elif type == "categories":
        note1in = 'in the category'
    output += '<ul><li id="note1">Note 1: This figure can be greater than the total bytes %s, as byte erased are not discounted in this ranking.</li></ul>' % (note1in)

    return output

def generatePagesTable(type=None, user_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "categories" and category_props)
    assert type != "pages" # no necesaria esta tabla para pages

    output = ''
    #legend
    output += smwhtml.getLegend()

    #table
    output += '<table class="prettytable"><tr>'
    output += '<th>#</th><th>Page</th><th>Namespace</th><th>Edits</th><th>%</th><th>Bytes</th><th>%</th>'
    if type == "global":
        output += '<th>Visits</th><th>%</th>'
    output += '</tr>'

    pagesSorted = []
    totalrevisions = 0
    totalbytes = 0
    totalvisits = 0
    if type == "global":
        pagesSorted = smwget.getPagesSortedByTotalRevisions()
        totalrevisions = smwget.getTotalRevisions()
        totalbytes = smwget.getTotalBytes()
        totalvisits = smwget.getTotalVisits()
    elif type == "users":
        pagesSorted = smwget.getPagesSortedByTotalRevisionsByUser(user_text_=user_props["user_name_"])
        totalrevisions = smwget.getTotalRevisionsByUser(user_text_=user_props["user_name_"])
        totalbytes = smwget.getTotalBytesByUser(user_text_=user_props["user_name_"])
    elif type == "categories":
        pagesSorted = smwget.getPagesSortedByTotalRevisionsByCategory(category_props=category_props)
        totalrevisions = smwget.getTotalRevisionsByCategory(category_props=category_props)
        totalbytes = smwget.getTotalBytesByCategory(category_props=category_props)

    c = 1
    acumrevisions = 0
    acumbytes = 0
    acumvisits = 0
    for numrevisions, page_id in pagesSorted:
        if type != "global" and numrevisions == 0:
            continue

        page_props = smwconfig.pages[page_id]

        #start row
        output += '<tr><td>%d</td>' % (c)
        full_page_title = page_props["page_namespace"] == 0 and page_props["page_title"] or '%s:%s' % (smwconfig.namespaces[page_props["page_namespace"]], page_props["page_title"])
        full_page_title_ = re.sub(' ', '_', full_page_title)
        output += '<td><a href="%s/pages/page_%d.html">%s</a></td><td>%s</td>' % (type == "global" and 'html' or '..', page_id, full_page_title, smwconfig.namespaces[smwconfig.pages[page_id]["page_namespace"]])

        #revisions
        maxi = 0
        if type == "global":
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalRevisions()] + [0]))
        elif type == "users":
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalRevisionsByUser(user_text_=user_props["user_name_"])] + [0]))
        elif type == "categories":
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalRevisionsByCategory(category_props=category_props)] + [0]))
        acumrevisions += numrevisions
        percent = totalrevisions > 0 and numrevisions/(totalrevisions/100.0) or 0
        color = maxi and numrevisions/(maxi/smwconfig.preferences["numColors"]) or 0
        output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f</td>' % (color, numrevisions, color, percent)

        #bytes
        numbytes = 0
        maxi = 0
        if type == "global":
            numbytes = page_props["page_len"]
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalBytes()] + [0]))
        elif type == "users":
            numbytes = smwget.getTotalBytesByUserInPage(user_text_=user_props["user_name_"], page_id=page_id)
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalBytesByUser(user_props=user_props)] + [0]))
        elif type == "categories":
            numbytes = page_props["page_len"]
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalBytesByCategory(category_props=category_props)] + [0]))
        acumbytes += numbytes
        percent = totalbytes > 0 and numbytes/(totalbytes/100.0) or 0
        color = maxi and numbytes/(maxi/smwconfig.preferences["numColors"]) or 0
        output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numbytes, color, percent)

        #visits
        maxi = 0
        if type == "global":
            acumvisits += page_props["page_counter"]
            percent = totalvisits > 0 and page_props["page_counter"]/(totalvisits/100.0) or 0
            maxi = float(max([k for k, v in smwget.getPagesSortedByTotalVisits()] + [0]))
            color = maxi and page_props["page_counter"]/(maxi/smwconfig.preferences["numColors"]) or 0
            output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, page_props["page_counter"], color, percent)

        #end row
        output += '</tr>\n'
        c += 1

    #total row
    output += '<tr><td colspan="3">Total</td>'
    output += '<td>%d</td><td>%.1f%%</td>' % (acumrevisions, totalrevisions and acumrevisions/(totalrevisions/100.0) or 0)
    output += '<td>%d</td><td>%.1f%%</td>' % (acumbytes, totalbytes and acumbytes/(totalbytes/100.0) or 0)
    if type == "global":
        output += '<td>%d</td><td>%.1f%%</td>' % (acumvisits, totalvisits and acumvisits/(totalvisits/100.0) or 0)
    output += '</tr>'
    output += '</table>'

    return output

def generateCategoriesTable():
    output = """<table class="prettytable">
    <tr><th>#</th><th>Category</th><th>Pages</th><th>%</th><th>Edits</th><th>%</th><th>Bytes</th><th>%</th><th>Visits</th><th>%</th></tr>"""

    categoriesSorted = [] #by edits

    all_categorised_page_ids = set() #a set to avoid dupes
    for category_title_, category_props in smwconfig.categories.items():
        if category_props["category_id"] != None: #si la página de la categoría existe
            [all_categorised_page_ids.add(i) for i in category_props["pages"]]

    totaledits = 0
    totalbytes = 0
    totalvisits = 0
    for page_id, page_props in smwconfig.pages.items():
        if page_id in all_categorised_page_ids: #for the totals, only count categorised pages info
            totaledits += smwget.getTotalRevisionsByPage(page_id=page_id)
            totalbytes += page_props["page_len"]
            totalvisits += page_props["page_counter"]
    totalpages = len(all_categorised_page_ids)

    for category_title_, category_props in smwconfig.categories.items():
        categoriesSorted.append([len(category_props["pages"]), category_title_])
    categoriesSorted.sort()
    categoriesSorted.reverse()

    c = 1
    for numpages, category_title_ in categoriesSorted:
        category_props = smwconfig.categories[category_title_]
        if category_props["category_id"] == None: #categorías que contienen páginas pero que no tienen página creada, por lo tanto no tienen page_id
            continue

        #acumulado para las páginas de esta categoría
        numedits = 0
        numbytes = 0
        numvisits = 0
        for page_id, page_props in smwconfig.pages.items():
            if page_id in category_props["pages"]:
                numedits += smwget.getTotalRevisionsByPage(page_id=page_id)
                numbytes += page_props["page_len"]
                numvisits += page_props["page_counter"]

        numvisitspercent = 0
        if totalvisits > 0:
            numvisitspercent = numvisits/(totalvisits/100.0)

        output += '<tr>'
        output += '<td>%d</td><td><a href="html/categories/category_%d.html">%s</a></td>' % (c, category_props["category_id"], category_props["category_title"])
        output += '<td>%d</td><td>%.1f%%</td>' % (numpages, totalpages and numpages/(totalpages/100.0) or 0)
        output += '<td>%d</td><td>%.1f%%</td>' % (numedits, totaledits and numedits/(totaledits/100.0) or 0)
        output += '<td>%d</td><td>%.1f%%</td>' % (numbytes, totalbytes and numbytes/(totalbytes/100.0) or 0)
        output += '<td>%d</td><td>%.1f%%</td>' % (numvisits, totalvisits and numvisits/(totalvisits/100.0) or 0)
        output += '</tr>\n'
        c += 1

    output += '<tr><td></td><td>Total</td><td>%d</td><td>100%%</td><td>%d</td><td>100%%</td><td>%d</td><td>100%%</td><td>%d</td><td>100%%</td></tr>\n' % (totalpages, totaledits, totalbytes, totalvisits)
    output += '</table>'
    output += '<center>Due to some pages can be contained in various categories, the sum of the colums can be different to the total row</center>'

    return output

def generateGlobalAnalysis():
    print "Generating global analysis"
    body = """%s

    %s

    <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>
    <div id="divcontentevolution">
    <table class="prettytable downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/global/global_content_evolution.png">PNG</a></td></tr>
    <tr><td><a href="csv/global/global_content_evolution.csv">CSV</a></td></tr>
    </table>
    <center>
    <img src="graphs/global/global_content_evolution.png" alt="Content evolution" />
    </center>
    </div>

    <h2 id="activity"><span class="showhide">[ <a href="javascript:showHide('divactivity')">Show/Hide</a> ]</span>Activity</h2>
    <div id="divactivity">
    <center>
    <table class="prettytable downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/global/global_hour_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/global/global_hour_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/global/global_hour_activity.png" alt="Hour activity" /><br/>

    <table class="prettytable downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/global/global_dayofweek_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/global/global_dayofweek_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/global/global_dayofweek_activity.png" alt="Day of week activity" /><br/>

    <table class="prettytable downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/global/global_month_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/global/global_month_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/global/global_month_activity.png" alt="Month activity" />
    </center>
    </div>

    <h2 id="topusers"><span class="showhide">[ <a href="javascript:showHide('divusers')">Show/Hide</a> ]</span>Users</h2>
    <div id="divusers">
    <center>
    %s
    </center>
    </div>

    <h2 id="toppages"><span class="showhide">[ <a href="javascript:showHide('divpages')">Show/Hide</a> ]</span>Pages</h2>
    <div id="divpages">
    <center>
    %s
    </center>
    </div>

    <h2 id="topcategories"><span class="showhide">[ <a href="javascript:showHide('divcategories')">Show/Hide</a> ]</span>Categories</h2>
    <div id="divcategories">
    <p>This analysis includes pages aggregated by categories.</p>
    <center>
    %s
    </center>
    </div>

    <h2 id="tagscloud"><span class="showhide">[ <a href="javascript:showHide('divtagscloud')">Show/Hide</a> ]</span>Tags cloud</h2>
    <div id="divtagscloud">
    <center>
    %s
    </center>
    </div>
    """ % (smwhtml.getSections(type="global"), generateSummary(type="global"), generateUsersTable(type="global"), generatePagesTable(type="global"), generateCategoriesTable(), generateCloud(type="global"))

    generateContentEvolution(type="global")
    generateGlobalTimeActivity()

    smwhtml.printHTML(type="global", title=smwconfig.preferences["siteName"], body=body)

def generateUsersAnalysis():
    for user_name_, user_props in smwconfig.users.items():
        print "Generating analysis to user: %s" % user_props["user_name"]
        generateContentEvolution(type="users", user_props=user_props)
        if smwconfig.preferences["anonymous"]:
            continue
        generateUsersTimeActivity(user_props=user_props)

        gallery = ''
        for img_name_ in smwget.getImagesByUser(user_text_=user_name_):
            gallery += """<a href='%s/%s/Image:%s'><img src="%s" width="200px" alt="%s"/></a>&nbsp;&nbsp;&nbsp;""" % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], img_name_, smwconfig.images[img_name_]["img_url"], img_name_)

        filesubfix = user_props["user_id"]
        if filesubfix == 0: #ip
            filesubfix = user_name_

        body = """%s\n%s\n%s


        <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>

        <div id="divcontentevolution">
        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_content_evolution.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_content_evolution.csv">CSV</a></td></tr>
        </table>
        <center>
        <img src="../../graphs/users/user_%s_content_evolution.png" alt="Content evolution" />
        </center>
        </div>

        <h2 id="activity"><span class="showhide">[ <a href="javascript:showHide('divactivity')">Show/Hide</a> ]</span>Activity</h2>

        <div id="divactivity">
        <center>
        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_hour_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_hour_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/users/user_%s_hour_activity.png" alt="Hour activity" /><br/>

        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_dayofweek_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_dayofweek_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/users/user_%s_dayofweek_activity.png" alt="Day of week activity" /><br/>

        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/users/user_%s_month_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/users/user_%s_month_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/users/user_%s_month_activity.png" alt="Month activity" />
        </center>
        </div>

        <h2 id="toppages"><span class="showhide">[ <a href="javascript:showHide('divmostedited')">Show/Hide</a> ]</span>Most edited pages</h2>
        <div id="divmostedited">
        <center>
        %s
        </center>
        </div>

        <h2 id="uploads"><span class="showhide">[ <a href="javascript:showHide('divuploads')">Show/Hide</a> ]</span>Uploads</h2>
        <div id="divuploads">
        This user has uploaded %s files.<br/>
        <center>
        %s
        </center>
        </div>

        <h2 id="tagscloud"><span class="showhide">[ <a href="javascript:showHide('divtagscloud')">Show/Hide</a> ]</span>Tags cloud</h2>
        <div id="divtagscloud">
        <center>
        %s
        </center>
        </div>

        %s
        """ % (smwhtml.getBacklink(), smwhtml.getSections(type="users"), generateSummary(type="users", user_props=user_props), filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, filesubfix, generatePagesTable(type="users", user_props=user_props), smwget.getTotalImagesByUser(user_text_=user_name_), gallery, generateCloud(type="users", user_props=user_props), smwhtml.getBacklink())

        title = "%s: User:%s" % (smwconfig.preferences["siteName"], user_props["user_name"])
        if not smwconfig.preferences["anonymous"]:
            smwhtml.printHTML(type="users", file="user_%s.html" % filesubfix, title=title, body=body)

def generatePagesAnalysis():
    for page_id, page_props in smwconfig.pages.items():
        print "Generating analysis to the page: %s" % (page_props["full_page_title"])
        generateContentEvolution(type="pages", page_props=page_props)
        generatePagesTimeActivity(page_props=page_props)
        generatePagesWorkDistribution(page_props=page_props)

        body = """%s\n%s\n%s

        <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>
        <div id="divcontentevolution">
        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_content_evolution.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_content_evolution.csv">CSV</a></td></tr>
        </table>
        <center>
        <img src="../../graphs/pages/page_%s_content_evolution.png" alt="Content evolution" />
        </center>
        </div>

        <h2 id="activity"><span class="showhide">[ <a href="javascript:showHide('divactivity')">Show/Hide</a> ]</span>Activity</h2>
        <div id="divactivity">
        <center>
        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_hour_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_hour_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/pages/page_%s_hour_activity.png" alt="Hour activity" /><br/>

        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_dayofweek_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_dayofweek_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/pages/page_%s_dayofweek_activity.png" alt="Day of week activity" /><br/>

        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/pages/page_%s_month_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/pages/page_%s_month_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/pages/page_%s_month_activity.png" alt="Month activity" />
        </center>
        </div>

        <h2 id="workdistribution"><span class="showhide">[ <a href="javascript:showHide('divworkdistribution')">Show/Hide</a> ]</span>Work distribution</h2>
        <div id="divworkdistribution">
        <center>
        <img src="../../graphs/pages/page_%s_work_distribution.png" alt="Work distribution" />
        </center>

        <h2 id="topusers"><span class="showhide">[ <a href="javascript:showHide('divtopusers')">Show/Hide</a> ]</span>Top users</h2>
        <div id="divtopusers">
        <center>
        %s
        </center>
        </div>

        <h2 id="tagscloud"><span class="showhide">[ <a href="javascript:showHide('divtagscloud')">Show/Hide</a> ]</span>Tags cloud</h2>
        <div id="divtagscloud">
        <center>
        %s
        </center>
        </div>
        &lt;&lt; <a href="../../%s">Back</a>
        """ % (smwhtml.getBacklink(), smwhtml.getSections(type='pages'), generateSummary(type="pages", page_props=page_props), page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, generateUsersTable(type="pages", page_props=page_props), generateCloud(type="pages", page_props=page_props), smwconfig.preferences["indexFilename"])

        title = "%s: %s" % (smwconfig.preferences["siteName"], page_props["full_page_title"])
        smwhtml.printHTML(type="pages", file="page_%d.html" % page_id, title=title, body=body)

def generateCategoriesAnalysis():
    for category_title_, category_props in smwconfig.categories.items():
        if category_props["category_id"] == None:
            #necesitamos un page_id para la categoría, para los nombres de los ficheros, no nos lo vamos a inventar
            #así que si no existe, no generamos análisis para esa categoría
            print "Some pages are categorised into %s but there is no page for that category" % (category_title_)
            continue
        print "Generating analysis to the category: %s" % category_title_
        generateContentEvolution(type="categories", category_props=category_props)
        generateCategoriesTimeActivity(category_props=category_props)
        generateCategoriesWorkDistribution(category_props=category_props)

        body = """%s\n%s\n%s

        <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>
        <div id="divcontentevolution">
        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_content_evolution.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_content_evolution.csv">CSV</a></td></tr>
        </table>
        <center>
        <img src="../../graphs/categories/category_%d_content_evolution.png" alt="Content evolution" />
        </center>
        </div>

        <h2 id="activity"><span class="showhide">[ <a href="javascript:showHide('divactivity')">Show/Hide</a> ]</span>Activity</h2>
        <div id="divactivity">
        <center>
        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_hour_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_hour_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/categories/category_%d_hour_activity.png" alt="Hour activity" /><br/>

        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_dayofweek_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_dayofweek_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/categories/category_%d_dayofweek_activity.png" alt="Day of week activity" /><br/>

        <table class="prettytable downloads">
        <tr><th><b>Download as</b></th></tr>
        <tr><td><a href="../../graphs/categories/category_%d_month_activity.png">PNG</a></td></tr>
        <tr><td><a href="../../csv/categories/category_%d_month_activity.csv">CSV</a></td></tr>
        </table>
        <img src="../../graphs/categories/category_%d_month_activity.png" alt="Month activity" />
        </center>
        </div>

        <h2 id="workdistribution"><span class="showhide">[ <a href="javascript:showHide('divworkdistribution')">Show/Hide</a> ]</span>Work distribution</h2>
        <div id="divworkdistribution">
        <center>
        <img src="../../graphs/categories/category_%s_work_distribution.png" alt="Work distribution" />
        </center>

        <h2 id="topusers"><span class="showhide">[ <a href="javascript:showHide('divtopusers')">Show/Hide</a> ]</span>Top users</h2>
        <div id="divtopusers">
        <center>
        %s
        </center>
        </div>

        <h2 id="toppages"><span class="showhide">[ <a href="javascript:showHide('divtoppages')">Show/Hide</a> ]</span>Top pages</h2>
        <div id="divtoppages">
        <center>
        %s
        </center>
        </div>

        <h2 id="tagscloud"><span class="showhide">[ <a href="javascript:showHide('divtagscloud')">Show/Hide</a> ]</span>Tags cloud</h2>
        <div id="divtagscloud">
        <center>
        %s
        </center>
        </div>
        &lt;&lt; <a href="../../%s">Back</a>
        """ % (smwhtml.getBacklink(), smwhtml.getSections(type="categories"), generateSummary(type="categories", category_props=category_props), category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], generateUsersTable(type="categories", category_props=category_props), generatePagesTable(type="categories", category_props=category_props), generateCloud(type="categories", category_props=category_props), smwconfig.preferences["indexFilename"]) #crear topuserstable para las categorias y fusionarla con generatePagesTopUsersTable(page_id=page_id) del las páginas y el global (así ya todas muestran los incrementos en bytes y porcentajes, además de la ediciones), lo mismo para el top de páginas más editadas

        title = "%s: Pages in category %s" % (smwconfig.preferences["siteName"], category_props["category_title"])
        smwhtml.printHTML(type="categories", file="category_%d.html" % category_props["category_id"], title=title, body=body)

