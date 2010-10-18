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

def generateTimeActivity(timesplit, type, fileprefix, conds, headers, user_props=None, page_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)
    results = {}

    conn, cursor = smwdb.createConnCursor()
    for cond in conds:
        cursor.execute("SELECT %s(rev_timestamp) AS time, COUNT(rev_id) AS count FROM %srevision, %spage WHERE rev_page=page_id and %s GROUP BY time ORDER BY time" % (timesplit, smwconfig.preferences["tablePrefix"], smwconfig.preferences["tablePrefix"], cond))
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
    if type=="global":
        if timesplit == "hour":
            title = u"Hour activity in %s" % smwconfig.preferences["siteName"]
        elif timesplit == "dayofweek":
            title = u"Day of week activity in %s" % smwconfig.preferences["siteName"]
        elif timesplit == "month":
            title = u"Month activity in %s" % smwconfig.preferences["siteName"]
    elif type == "users":
        if timesplit == "hour":
            title = u"Hour activity by %s" % user_props["user_name"]
        elif timesplit == "dayofweek":
            title = u"Day of week activity by %s" % user_props["user_name"]
        elif timesplit == "month":
            title = u"Month activity by %s" % user_props["user_name"]
    elif type == "pages":
        if timesplit == "hour":
            title = u"Hour activity in %s" % page_props["page_title"]
        elif timesplit == "dayofweek":
            title = u"Day of week activity in %s" % page_props["page_title"]
        elif timesplit == "month":
            title = u"Month activity in %s" % page_props["page_title"]
    elif type == "categories":
        if timesplit == "hour":
            title = u"Hour activity in category %s" % category_props["category_title"]
        elif timesplit == "dayofweek":
            title = u"Day of week activity in category %s" % category_props["category_title"]
        elif timesplit == "month":
            title = u"Month activity in category %s" % category_props["category_title"]

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
    full_page_title = page_props["page_title"]
    if page_props["page_namespace"] != 0:
        full_page_title = '%s:%s' % (page_props["page_namespace"], page_props["page_title"])
    conds = ["1 and rev_page=%d" % page_props["page_id"], "rev_user=0 and rev_page=%d" % page_props["page_id"], "rev_user!=0 and rev_page=%d" % page_props["page_id"]] #todas, anónimas o registrados
    headers = ["Edits in %s (all users)" % full_page_title, "Edits in %s (only anonymous users)" % full_page_title, "Edits in %s (only registered users)" % full_page_title]
    generateTimeActivity(timesplit="hour", type="pages", fileprefix="page_%d" % page_props["page_id"], conds=conds, headers=headers, page_props=page_props)
    generateTimeActivity(timesplit="dayofweek", type="pages", fileprefix="page_%d" % page_props["page_id"], conds=conds, headers=headers, page_props=page_props)
    generateTimeActivity(timesplit="month", type="pages", fileprefix="page_%d" % page_props["page_id"], conds=conds, headers=headers, page_props=page_props)

def generateCategoriesTimeActivity(category_props=None): #fix category_props
    assert category_props
    conds2 = ["1", "rev_user=0", "rev_user!=0"] #todas, anónimas o registrados
    conds = []
    for cond in conds2:
        conds.append("%s and rev_page in (select cl_from from categorylinks where cl_to='%s')" % (cond, category_props["category_title_"].encode("utf-8"))) #fix cuidado con nombres de categorías con '
    headers = ["Edits in category %s (all users)" % category_props["category_title"], "Edits in category %s (only anonymous users)" % category_props["category_title"], "Edits in category %s (only registered users)" % category_props["category_title"]]
    generateTimeActivity(timesplit="hour", type="categories", fileprefix="category_%d" % category_props["category_id"], conds=conds, headers=headers, category_props=category_props)
    generateTimeActivity(timesplit="dayofweek", type="categories", fileprefix="category_%d" % category_props["category_id"], conds=conds, headers=headers, category_props=category_props)
    generateTimeActivity(timesplit="month", type="categories", fileprefix="category_%d" % category_props["category_id"], conds=conds, headers=headers, category_props=category_props)

def generateUsersTimeActivity(user_props=None):
    assert user_props
    conds = ["rev_user_text='%s'" % user_props["user_name"].encode("utf-8"), "page_namespace=0 and rev_user_text='%s'" % user_props["user_name"].encode("utf-8"), "page_namespace=1 and rev_user_text='%s'" % user_props["user_name"].encode("utf-8")] # artículo o todas, #todo añadir escape() para comillas?
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
        output += u"There is no comments in edits."

    return output

def generateTableByNamespace(htmlid=None, fun=None):
    assert htmlid and fun
    output = '[<a href="javascript:showHide(\'%s\')">Show/Hide</a>]\n<div id="%s" style="display: none;"><table>' % (htmlid, htmlid)
    namespaces = smwconfig.namespaces.items()
    namespaces.sort()
    for nmnum, nmname in namespaces:
        output += '<tr><td><b>%s</b></td><td>%d</td></tr>' % (nmname, fun(namespace=nmnum))
    output += '</table></div>'
    return output

def generateSummary(type, user_props=None, page_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "pages" and page_props) or (type == "categories" and category_props)
    output = '<table class="summary">'

    if type == "global":
        output += '<tr><td><b>Site:</b></td><td><a href="%s">%s</a> (<a href="%s/%s/Special:Recentchanges">recent changes</a>)</td></tr>' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["siteName"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td>' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total pages:</b></td><td>%d %s</td></tr>' % (smwget.getTotalPages(), generateTableByNamespace(htmlid='global-pages', fun=smwget.getTotalPagesByNamespace))
        output += '<tr><td><b>Total edits:</b></td><td>%d %s</td></tr>' % (smwget.getTotalRevisions(), generateTableByNamespace(htmlid='global-edits', fun=smwget.getTotalRevisionsByNamespace))
        output += '<tr><td><b>Total bytes:</b></td><td>%d %s</td></tr>' % (smwget.getTotalBytes(), generateTableByNamespace(htmlid='global-bytes', fun=smwget.getTotalBytesByNamespace))
        output += '<tr><td><b>Total files:</b></td><td>%d</td></tr>' % (smwget.getTotalImages())
        output += '<tr><td><b>Total users:</b></td><td>%d</td></tr>' % (smwget.getTotalUsers())
        output += '<tr><td><b>Total visits:</b></td><td>%d %s</td></tr>' % (smwget.getTotalVisits(), generateTableByNamespace(htmlid='global-visits', fun=smwget.getTotalVisitsByNamespace))
    elif type == "users":
        output += '<tr><td><b>User:</b></td><td><a href="%s/%s/User:%s">%s</a> (<a href="%s/%s/Special:Contributions/%s">contributions</a>)</td></tr>' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], user_props["user_name_"], user_props["user_name"], smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], user_props["user_name_"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td>' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total pages edited:</b></td><td>%d</td></tr>' % (smwget.getTotalPagesByUser(user_text_=user_props["user_name_"]))#fix: renombrar a PagesEdited y hacer PagesCreated?
        output += '<tr><td><b>Total edits:</b></td><td>%d</td></tr>' % (smwget.getTotalRevisionsByUser(user_text_=user_props["user_name_"]))
        output += '<tr><td><b>Total bytes:</b></td><td>%d</td></tr>' % (smwget.getTotalBytesByUser(user_text_=user_props["user_name_"]))
        output += '<tr><td><b>Total files:</b></td><td>%d</td></tr>' % (smwget.getTotalImagesByUser(user_text_=user_props["user_name_"]))
    elif type == "pages":
        full_page_title = page_props["page_namespace"] == 0 and page_props["page_title"] or '%s:%s' % (smwconfig.namespaces[page_props["page_namespace"]], page_props["page_title"])
        full_page_title_ = re.sub(' ', '_', full_page_title)
        output += '<tr><td><b>Page:</b></td><td><a href="%s/%s/%s">%s</a> (<a href="%s/index.php?title=%s&amp;action=history">history</a>)</td></tr>' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], full_page_title_, full_page_title, smwconfig.preferences["siteUrl"], full_page_title_)
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td>' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total edits:</b></td><td>%d</td></tr>' % (smwget.getTotalRevisionsByPage(page_id=page_props["page_id"]))
        output += '<tr><td><b>Total bytes:</b></td><td>%d</td></tr>' % (page_props["page_len"])
    elif type == "categories":
        output += '<tr><td><b>Category:</b></td><td><a href="%s/%s/Category:%s">%s</a> (<a href="%s/index.php?title=Category:%s&amp;action=history">history</a>)</td></tr>' % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], category_props["category_title"], category_props["category_title"], smwconfig.preferences["siteUrl"], category_props["category_title"])
        output += '<tr><td><b>Report period:</b></td><td>%s &ndash; %s</td>' % (smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat())
        output += '<tr><td><b>Total pages included:</b></td><td>%d</td></tr>' % (len(category_props["pages"]))
        output += '<tr><td><b>Total edits:</b></td><td>%d</td></tr>' % (smwget.getTotalRevisionsByCategory(category_props=category_props))

    output += '<tr><td><b>Generated in:</b></td><td>%s</td></tr>' % (datetime.datetime.now().isoformat())

    """title de site, user, page, category
    report period
    total pages (no aplica a pages)
    ediciones totales, in articles
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
    bytes totales, in articles
    número de usuarios (no aplica a users)
    ediciones promedio por usuario (no aplica a users)
    pareto número de ediciones hechas por el top 10% de usuarios (no aplica a users)
    número de ficheros
    generated in"""

    """
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
    </dl> (smwconfig.preferences["siteUrl"], smwconfig.preferences["siteName"], smwconfig.preferences["startDate"].isoformat(), smwconfig.preferences["endDate"].isoformat(), totalpages, totalarticles, totalarticlespercent, totaledits, totaleditsinarticles, totaleditsinarticlespercent, totalbytes, totalbytesinarticles, totalbytesinarticlespercent, totalvisits, totalvisitsinarticles, totalvisitsinarticlespercent, smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], totalfiles, totalusers, datetime.datetime.now().isoformat(), generateUsersTable(), generatePagesTable(), generateCategoriesTable(), generateGlobalCloud())


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

    title = ''
    fileprefix = ''
    owner = ''
    if type == "global":
        title = u"Content evolution in %s" % smwconfig.preferences["siteName"]
        fileprefix = "global"
        owner = smwconfig.preferences["siteName"]
    elif type == "users":
        title = u"Content evolution by %s" % user_props["user_name"]
        if user_props["user_id"] == 0:
            fileprefix = "user_%s" % user_props["user_name_"]
        else:
            fileprefix = "user_%s" % user_props["user_id"]
        owner = user_props["user_name"]
    elif type == "pages":
        title = u"Content evolution in %s" % page_props["page_title"]
        fileprefix = "page_%s" % page_props["page_id"]
        owner = page_props["page_title"]
    elif type == "categories":
        title = u"Content evolution for pages in %s" % category_props["category_title"]
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
        return u"""<p>This is an anonymous analysis. This information will not be showed.</p>\n"""

    output = ''
    #legend
    output += smwhtml.getLegend()

    #table
    output += '<table><tr>'
    output += '<th>#</th><th>User</th><th>Edits</th><th>%</th>'
    if type != "pages": # no tiene sentido dentro de páginas
        output += '<th>Edits in articles</th><th>%</th>'
    output += '<th>Bytes added</th><th>%</th>'
    if type != "pages":
        output += '<th>Bytes added in articles</th><th>%</th>'
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
        pass
    else:
        print "Error type =", type
        sys.exit()

    c = 1
    acumrevisions = 0
    acumrevisionsinarticles = 0
    acumbytes = 0
    acumbytesinarticles = 0
    acumuploads = 0
    for numrevisions, user_text_ in usersSorted:
        filesubfix = smwconfig.users[user_text_]["user_id"]
        if filesubfix == 0: #ip
            filesubfix = user_text_

        #start row
        output += '<tr><td>%d</td>' % (c)
        output += '<td><a href="%s/users/user_%s.html">%s</a></td>' % (type == "global" and 'html' or '..', filesubfix, smwconfig.users[user_text_]["user_name"])
        #revisions
        acumrevisions += numrevisions
        percent = totalrevisions > 0 and numrevisions/(totalrevisions/100.0) or 0
        maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisions()] + [0]))
        color = maxi and numrevisions/(maxi/smwconfig.preferences["numColors"]) or 0
        output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numrevisions, color, percent)
        #revisions in articles
        if type == "global":
            numrevisionsinarticles = smwget.getTotalRevisionsByUserInNamespace(user_text_=user_text_, namespace=0)
            acumrevisionsinarticles += numrevisionsinarticles
            percent = totalrevisionsinarticles > 0 and numrevisionsinarticles/(totalrevisionsinarticles/100.0) or 0
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalRevisionsInNamespace(namespace=0)] + [0]))
            color = maxi and numrevisionsinarticles/(maxi/smwconfig.preferences["numColors"]) or 0
            output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numrevisionsinarticles, color, percent)
        elif type == "pages":
            pass #no required
        elif type == "categories":
            pass #todo
        #bytes
        numbytes = 0
        maxi = 0
        if type == "global":
            numbytes = smwget.getTotalBytesByUser(user_text_=user_text_)
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytes()] + [0]))
        elif type == "pages":
            numbytes = smwget.getTotalBytesByUserInPage(user_text_=user_text_, page_id=page_props["page_id"])
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytesInPage(page_id=page_props["page_id"])] + [0]))
        elif type == "category":
            pass #todo
        acumbytes += numbytes
        percent = totalbytes > 0 and numbytes/(totalbytes/100.0) or 0
        color = maxi and numbytes/(maxi/smwconfig.preferences["numColors"]) or 0
        output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numbytes, color, percent)
        #bytes in articles
        if type == "global":
            numbytesinarticles = smwget.getTotalBytesByUserInNamespace(user_text_=user_text_, namespace=0)
            acumbytesinarticles += numbytesinarticles
            percent = totalbytesinarticles > 0 and numbytesinarticles/(totalbytesinarticles/100.0) or 0
            maxi = float(max([k for k, v in smwget.getUsersSortedByTotalBytesInNamespace(namespace=0)] + [0]))
            color = maxi and numbytesinarticles/(maxi/smwconfig.preferences["numColors"]) or 0
            output += '<td class="cellcolor%d">%d</td><td class="cellcolor%d">%.1f%%</td>' % (color, numbytesinarticles, color, percent)
        elif type == "pages":
            pass #no required
        elif type == "categories":
            pass #todo
        #uploads
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
    output += '<td>%d</td><td>%.1f%%<sup>[<a href="#note1">1</a>]</sup></td>' % (acumbytes, totalbytes and acumbytes/(totalbytes/100.0) or 0)
    if type != "pages":
        output += '<td>%d</td><td>%.1f%%<sup>[<a href="#note1">1</a>]</sup></td>' % (acumbytesinarticles, totalbytesinarticles and acumbytesinarticles/(totalbytesinarticles/100.0) or 0)
    if type == "global":
        output += '<td>%d</td><td>%.1f%%</td>' % (acumuploads, totaluploads and acumuploads/(totaluploads/100.0) or 0)
    output += '</tr>'

    #<td>%s (100%%)</td><td>%s (100%%)</td><td>%s<sup>[<a href="#note1">note 1</a>]</sup> (100%%)</td><td>%s</td></tr>\n'
    output += '</table>'

    #notes
    output += '<ul><li id="note1">Note 1: This figure can be greater than the total bytes in the wiki, as byte erased are not discounted in this ranking.</li></ul>'

    return output

def generatePagesTable(type=None, user_props=None, category_props=None):
    assert type == "global" or (type == "users" and user_props) or (type == "categories" and category_props)
    assert type != "pages" # no necesaria esta tabla para pages

    output = ''
    #legend
    output += smwhtml.getLegend()

    #table
    output += '<table><tr>'
    output += '<th>#</th><th>Page</th><th>Namespace</th><th>Edits</th><th>%</th><th>Bytes</th><th>%</th>'
    if type == "global":
        output += '<th>Visits</th><th>%</th>'
    output += '</tr>'

    pagesSorted = [] #by edits
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
        pass
    else:
        print "Error type =", type
        sys.exit()

    c = 1
    for numrevisions, page_id in pagesSorted:
        page_props = smwconfig.pages[page_id]
        #start row
        output += '<tr><td>%d</td>' % (c)
        full_page_title = page_props["page_namespace"] == 0 and page_props["page_title"] or '%s:%s' % (smwconfig.namespaces[page_props["page_namespace"]], page_props["page_title"])
        full_page_title_ = re.sub(' ', '_', full_page_title)
        output += '<td><a href="%s/pages/page_%d.html">%s</a></td><td>%s</td>' % (type == "global" and 'html' or '..', page_id, full_page_title, smwconfig.namespaces[smwconfig.pages[page_id]["page_namespace"]])
        #edits
        output += '<td>%d</td><td>%.1f</td>' % (numrevisions, totalrevisions > 0 and numrevisions/(totalrevisions/100.0) or 0)
        #bytes
        numbytes = 0
        if type == "global":
            numbytes = page_props["page_len"]
        elif type == "users":
            numbytes = smwget.getTotalBytesByUserInPage(user_text_=user_props["user_name_"], page_id=page_id)
        elif type == "categories":
            pass #todo
        output += '<td>%d</td><td>%.1f%%</td>' % (numbytes, totalbytes > 0 and numbytes/(totalbytes/100.0) or 0)
        if type == "global":
            output += '<td>%d</td><td>%.1f%%</td>' % (page_props["page_counter"], totalvisits > 0 and page_props["page_counter"]/(totalvisits/100.0) or 0)
        #end row
        output += '</tr>\n'
        c += 1

    #output += '<tr><td></td><td>Total</td><td></td><td>%s (100%%)</td><td>%s (100%%)</td><td>%s (100%%)</td></tr>\n'
    output += '</table>'

    return output

def generateCategoriesTable():
    output = u"""<table>
    <tr><th>#</th><th>Category</th><th>Pages</th><th>%</th><th>Edits</th><th>%</th><th>Bytes</th><th>%</th><th>Visits</th><th>%</th></tr>"""

    categoriesSorted = [] #by edits

    all_categorised_page_ids = set()
    for category_title_, category_props in smwconfig.categories.items(): #fix page_ids es pages incluido dentro de category props
        if category_props["category_id"] != None: #si la página de la categoría existe
            [all_categorised_page_ids.add(i) for i in category_props["pages"]] #a set to avoid dupes

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
    body = u"""%s

    %s

    <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>
    <div id="divcontentevolution">
    <table class="downloads">
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
    <table class="downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/global/global_hour_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/global/global_hour_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/global/global_hour_activity.png" alt="Hour activity" /><br/>

    <table class="downloads">
    <tr><th><b>Download as</b></th></tr>
    <tr><td><a href="graphs/global/global_dayofweek_activity.png">PNG</a></td></tr>
    <tr><td><a href="csv/global/global_dayofweek_activity.csv">CSV</a></td></tr>
    </table>
    <img src="graphs/global/global_dayofweek_activity.png" alt="Day of week activity" /><br/>

    <table class="downloads">
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
        print u"Generating analysis to user: %s" % user_props["user_name"]
        generateContentEvolution(type="users", user_props=user_props)
        if smwconfig.preferences["anonymous"]:
            continue
        generateUsersTimeActivity(user_props=user_props)

        gallery = ''
        for img_name_ in smwget.getImagesByUser(user_text_=user_name_):
            gallery += u"""<a href='%s/%s/Image:%s'><img src="%s" width="200px" alt="%s"/></a>&nbsp;&nbsp;&nbsp;""" % (smwconfig.preferences["siteUrl"], smwconfig.preferences["subDir"], img_name_, smwconfig.images[img_name_]["img_url"], img_name_)

        filesubfix = user_props["user_id"]
        if filesubfix == 0: #ip
            filesubfix = user_name_

        body = u"""%s\n%s\n%s


        <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>

        <div id="divcontentevolution">
        <table class="downloads">
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
        print u"Generating analysis to the page: %s" % (page_props["page_title"])
        generateContentEvolution(type="pages", page_props=page_props)
        generatePagesTimeActivity(page_props=page_props)

        body = """%s\n%s\n%s

        <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>
        <div id="divcontentevolution">
        <table class="downloads">
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
        </div>

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
        """ % (smwhtml.getBacklink(), smwhtml.getSections(type='pages'), generateSummary(type="pages", page_props=page_props), page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, page_id, generateUsersTable(type="pages", page_props=page_props), generateCloud(type="pages", page_props=page_props), smwconfig.preferences["indexFilename"])

        title = "%s: %s" % (smwconfig.preferences["siteName"], page_props["page_title"])
        smwhtml.printHTML(type="pages", file="page_%d.html" % page_id, title=title, body=body)

def generateCategoriesAnalysis():
    for category_title_, category_props in smwconfig.categories.items(): #fix category_props en vez de page_ids
        if category_props["category_id"] == None:
            #necesitamos un page_id para la categoría, para los nombres de los ficheros, no nos lo vamos a inventar
            #así que si no existe, no generamos análisis para esa categoría
            print "Some pages are categorised into %s but there is no page for that category" % (category_title_)
            continue
        print u"Generating analysis to the category: %s" % category_title_
        generateContentEvolution(type="categories", category_props=category_props)
        generateCategoriesTimeActivity(category_props=category_props)

        body = u"""%s\n%s\n%s

        <h2 id="contentevolution"><span class="showhide">[ <a href="javascript:showHide('divcontentevolution')">Show/Hide</a> ]</span>Content evolution</h2>
        <div id="divcontentevolution">
        <table class="downloads">
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
        </div>

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
        """ % (smwhtml.getBacklink(), smwhtml.getSections(type="categories"), generateSummary(type="categories", category_props=category_props), category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], category_props["category_id"], "", "", generateCloud(type="categories", category_props=category_props), smwconfig.preferences["indexFilename"]) #crear topuserstable para las categorias y fusionarla con generatePagesTopUsersTable(page_id=page_id) del las páginas y el global (así ya todas muestran los incrementos en bytes y porcentajes, además de la ediciones), lo mismo para el top de páginas más editadas

        title = "%s: Pages in category %s" % (smwconfig.preferences["siteName"], category_props["category_title"])
        smwhtml.printHTML(type="categories", file="category_%d.html" % category_props["category_id"], title=title, body=body)

