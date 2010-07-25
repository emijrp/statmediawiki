#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010
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
import getopt
import Gnuplot
import md5
#import hashlib #From python2.5
import MySQLdb
import os
import re
import time
import shutil
import sys

images = {}
pages = {}
preferences = {}
users = {}
revisions = {}

preferences["outputDir"] = "output"
preferences["indexFilename"] = "index.html"
preferences["siteName"] = "YourWikiSite"
preferences["siteUrl"] = "http://youwikisite.org"
preferences["subDir"] = "/index.php" #MediaWiki subdir, usually index.php/
preferences["dbName"] = "yourwikidb"
preferences["tablePrefix"] = "" #Usually empty
preferences["startDate"] = "" #If wanted, start point for date range
preferences["endDate"] = "" #If wanted, end point for date range
preferences["currentPath"] = os.path.dirname(__file__)

#todo:
#con que numero se lanzan los sys.exit() cuando hay un fallo?
#que las rutas ../../ no sean relativas, buscar algo como $IP o __file__ ?

#el usuario que hace las consultas sql debe tener acceso lectura a las bbdd, con los datos de .my.cnf
t1=time.time()

def createConnCursor():
    conn = MySQLdb.connect(host='localhost', db=preferences["dbName"], read_default_file='/home/emijrp/.my.cnf', use_unicode=False) #pedir ruta absoluta del fichero cnf? #todo
    cursor = conn.cursor()
    try:
        conn = MySQLdb.connect(host='localhost', db=preferences["dbName"], read_default_file='/home/emijrp/.my.cnf', use_unicode=False) #pedir ruta absoluta del fichero cnf? #todo
        cursor = conn.cursor()
    except:
        print "Hubo un error al conectarse a la base de datos"
        sys.exit()
    return conn, cursor

def destroyConnCursor(conn, cursor):
    cursor.close()
    conn.close()

def getUserImages(user_id):
    user_images = []
    for img_name, imageprops in images.items():
        if imageprops["img_user"] == user_id:
            user_images.append(img_name)
    return user_images

def loadImages():
    global images
    images = {}
    
    conn, cursor = createConnCursor()
    cursor.execute("SELECT img_name, img_user, img_user_text, img_timestamp, img_size FROM %simage WHERE 1" % preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        img_name = unicode(re.sub("_", " ", row[0]), "utf-8")
        img_user = int(row[1])
        img_user_text = unicode(re.sub("_", " ", row[2]), "utf-8")
        img_timestamp = row[3]
        img_size = int(row[4])
        images[img_name] = {
            "img_user": img_user, 
            "img_user_text": img_user_text, 
            "img_timestamp": img_timestamp, 
            "img_size": img_size, 
        }
    print "Loaded %s images" % len(images.items())
    
    destroyConnCursor(conn, cursor)

def getUserRevisions(user_id):
    user_revisions = []
    
    user_name = users[user_id]["user_name"]
    for rev_id, rev_props in revisions.items():
        if user_name == rev_props["rev_user_text"]:
            user_revisions.append(rev_id)
    
    return user_revisions

def loadUsers():
    global users
    users = {}
    
    conn, cursor = createConnCursor()
    queries = [
        "SELECT DISTINCT rev_user, rev_user_text FROM %srevision WHERE 1" % (preferences["tablePrefix"]),
        "SELECT user_id, user_name FROM %suser WHERE 1" % (preferences["tablePrefix"]),
    ]
    for query in queries:
        cursor.execute(query)
        result = cursor.fetchall()
        for row in result:
            user_id = int(row[0])
            user_name = unicode(re.sub("_", " ", row[1]), "utf-8")
            if user_id == 0: #if ip, we use user_name (ip) as id
                user_id = user_name
            users[user_id] = {
                "user_name": user_name,
                "images": [],
                "revisions": [],
            }
    print "Loaded %s users" % len(users.items())
    
    #cargamos listas de images y revisiones para cada usuario
    #no puede hacerse en el bucle anterior porque getUserImages() y la otra función, llaman a users y necesitan que users esté creado antes
    for user_id, user_props in users.items():
        users[user_id]["images"] = getUserImages(user_id)
        users[user_id]["revisions"] = getUserRevisions(user_id)
    
    destroyConnCursor(conn, cursor)

def loadPages():
    global pages
    pages = {}
    
    conn, cursor = createConnCursor()
    cursor.execute("select page_id, page_namespace, page_title, page_is_redirect from %spage" % preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        page_id = int(row[0])
        page_namespace = int(row[1])
        page_title = unicode(row[2], "utf-8")
        page_is_redirect = int(row[3])
        pages[page_id] = {
            "page_namespace": page_namespace, 
            "page_title": page_title, 
            "page_is_redirect": page_is_redirect,
        }
    print "Loaded %s pages" % len(pages.items())
    
    destroyConnCursor(conn, cursor)

def loadRevisions():
    global revisions
    
    conn, cursor = createConnCursor()
    cursor.execute("select rev_id, rev_page, rev_user, rev_user_text, rev_timestamp, rev_comment, old_text from %srevision, %stext where old_id=rev_text_id and rev_timestamp>='%s' and rev_timestamp<='%s'" % (preferences["tablePrefix"], preferences["tablePrefix"], '%sZ000000T' % re.sub('-', '', preferences["startDate"].isoformat().split("T")[0]), '%sZ235959T' % re.sub('-', '', preferences["endDate"].isoformat().split("T")[0])))
    result = cursor.fetchall()
    for row in result:
        rev_id = int(row[0])
        rev_page = int(row[1])
        rev_user = int(row[2])
        rev_user_text = unicode(re.sub("_", " ", row[3]), "utf-8")
        rev_timestamp = row[4]
        rev_comment = unicode(row[5].tostring(), "utf-8")
        old_text = unicode(row[6].tostring(), "utf-8")
        revisions[rev_id] = {
            "rev_id": rev_id, #no es un error
            "rev_page": rev_page, 
            "rev_user": rev_user, 
            "rev_user_text": rev_user_text, 
            "rev_timestamp": datetime.datetime(year=int(rev_timestamp[:4]), month=int(rev_timestamp[4:6]), day=int(rev_timestamp[6:8]), hour=int(rev_timestamp[8:10]), minute=int(rev_timestamp[10:12]), second=int(rev_timestamp[12:14])), 
            "rev_comment": rev_comment, 
            "old_text": old_text, 
        } 
    print "Loaded %s revisions" % len(revisions.items())
    
    destroyConnCursor(conn, cursor)


def initialize():
    global preferences
    
    conn, cursor = createConnCursor()
    
    if not preferences["startDate"]:
        cursor.execute("SELECT rev_timestamp FROM %srevision ORDER BY rev_timestamp ASC LIMIT 1" % (preferences["tablePrefix"]))
        a = cursor.fetchall()[0][0]
        preferences["startDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=0, minute=0, second=0)
    
    if not preferences["endDate"]:
        cursor.execute("SELECT rev_timestamp FROM %srevision ORDER BY rev_timestamp DESC LIMIT 1" % (preferences["tablePrefix"]))
        a = cursor.fetchall()[0][0]
        preferences["endDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=0, minute=0, second=0)
    
    destroyConnCursor(conn, cursor)

def welcome():
    pass

def usage():
    f=open("help.txt", "r")
    print f.read()
    f.close()
    sys.exit() #mostramos ayuda y salimos

def getParameters():
    global preferences
    
    #console params
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["h", "help", "outputdir=", "index=", "sitename=", "subdir=", "siteurl=", "dbname=", "tableprefix=", "startdate=", "enddate="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("--outputdir"):
            preferences["outputDir"] = a
            while len(preferences["outputDir"])>0:
                if preferences["outputDir"][-1] == '/': #dará problemas con rutas windows?
                    preferences["outputDir"] = preferences["outputDir"][:-1]
                else:
                    break
        elif o in ("--index"):
            preferences["indexFilename"] = a
        elif o in ("--sitename"):
            preferences["siteName"] = a
        elif o in ("--siteurl"):
            preferences["siteUrl"] = a
        elif o in ("--subdir"):
            preferences["subDir"] = a
        elif o in ("--dbname"):
            preferences["dbName"] = a
        elif o in ("--tableprefix"):
            preferences["tablePrefix"] = a
        elif o in ("--startdate"):
            preferences["startDate"] = datetime.datetime(year=int(a.split("-")[0]), month=int(a.split("-")[1]), day=int(a.split("-")[2]), hour=0, minute=0, second=0)
        elif o in ("--enddate"):
            preferences["endDate"] = datetime.datetime(year=int(a.split("-")[0]), month=int(a.split("-")[1]), day=int(a.split("-")[2]), hour=0, minute=0, second=0)
        else:
            assert False, "unhandled option"

    #gestionar falta de parametros

    #fin gestionar falta parametros

def manageOutputDir():
    #Generando estructura de directorios
    directories = [
        preferences["outputDir"],
        "%s/csv" % preferences["outputDir"],
        "%s/csv/general" % preferences["outputDir"],
        "%s/csv/users" % preferences["outputDir"],
        "%s/csv/pages" % preferences["outputDir"],
        "%s/graphs" % preferences["outputDir"],
        "%s/graphs/general" % preferences["outputDir"],
        "%s/graphs/users" % preferences["outputDir"],
        "%s/graphs/pages" % preferences["outputDir"],
        "%s/html" % preferences["outputDir"],
        "%s/html/general" % preferences["outputDir"],
        "%s/html/users" % preferences["outputDir"],
        "%s/html/pages" % preferences["outputDir"],
        "%s/styles" % preferences["outputDir"],
    ]
    for directory in directories:
        if not os.path.exists(directory) or not os.path.isdir(directory):
            try:
                os.makedirs(directory)
                print "Creando %s" % directory
            except:
                print "Hubo un error al intentar crear la ruta %s" % directory
                sys.exit()

def copyFiles():
    #Copiando ficheros individuales
    #Van en el nivel principal (están duplicados con la línea anterior)
    os.system("cp %s/styles/*.css %s/styles" % (preferences["currentPath"], preferences["outputDir"]))
    #Los CSV no se copian, se generan directamente en outputdir
    #os.system("cp %s/csv/general/*.csv %s/csv/general" % (preferences["currentPath"], preferences["outputDir"]))
    #os.system("cp %s/csv/pages/*.csv %s/csv/pages" % (preferences["currentPath"], preferences["outputDir"]))
    #os.system("cp %s/csv/users/*.csv %s/csv/users" % (preferences["currentPath"], preferences["outputDir"]))
    
def printCSV(type, file, header, rows):
    #Type puede ser: general, users o pages
    #File es un nombre de fichero con extensión .
    f = open("%s/csv/%s/%s" % (preferences["outputDir"], type, file), "w")
    output = ",".join(header)
    output += "\n"
    f.write(output.encode("utf-8"))
    for row in rows:
        output = ",".join(row)
        output += "\n"
        f.write(output.encode("utf-8")) 
    f.close()

def generateTimeActivity(time, type, fileprefix, conds, headers, user_id=False, page_id=False):
    results = {}
    
    conn, cursor = createConnCursor()
    for cond in conds:
        cursor.execute("SELECT %s(rev_timestamp) AS time, COUNT(rev_id) AS count FROM %srevision INNER JOIN %spage ON rev_page=page_id WHERE %s GROUP BY time ORDER BY time" % (time, preferences["tablePrefix"], preferences["tablePrefix"], cond))
        result = cursor.fetchall()
        results[cond] = {}
        for timestamp, edits in result:
            if time in ["dayofweek", "month"]:
                timestamp = timestamp - 1
            results[cond][str(timestamp)] = str(edits)
    
    headers = [time] + headers
    fileprefix = "%s_%s" % (fileprefix, time)
    rows = []
    if time == "hour":
        range_ = range(24)
    elif time == "dayofweek":
        range_ = range(7)
    elif time == "month":
        range_ = range(12)
    
    row0=[]
    row1=[]
    row2=[]
    for period in range_:
        period  = str(period)
        row0.append(period)
        cond0 = "0"
        cond1 = "0"
        if results[conds[0]].has_key(period):
            cond0 = results[conds[0]][period]
        row1.append(cond0)
        if results[conds[1]].has_key(period):
            cond1 = results[conds[1]][period]
        row2.append(cond1)
    rows=[row0, row1, row2]
    
    title = ""
    if type=="general":
        if time=="hour":
            title = u"Hour activity in %s" % preferences["siteName"]
        elif time=="dayofweek":
            title = u"Day of week activity in %s" % preferences["siteName"]
        elif time=="month":
            title = u"Month activity in %s" % preferences["siteName"]
    elif type=="users":
        user_name = users[user_id]["user_name"]
        if time=="hour":
            title = u"Hour activity by %s" % user_name
        elif time=="dayofweek":
            title = u"Day of week activity by %s" % user_name
        elif time=="month":
            title = u"Month activity by %s" % user_name
    elif type=="pages":
        page_title = pages[page_id]["page_title"]
        if time=="hour":
            title = u"Hour activity in %s" % page_title
        elif time=="dayofweek":
            title = u"Day of week activity in %s" % page_title
        elif time=="month":
            title = u"Month activity in %s" % page_title
    
    #printCSV(type=type, file=file, header=header, rows=rows)
    print rows
    printGraphTimeActivity(type=type, fileprefix=fileprefix, title=title, headers=headers, rows=rows)
    
    destroyConnCursor(conn, cursor)

def generateGeneralTimeActivity():
    conds = ["1", "page_namespace=0"] # artículo o todas
    headers = ["Edits (all pages)", "Edits (only articles)"]
    generateTimeActivity(time="hour", type="general", fileprefix="general", conds=conds, headers=headers)
    generateTimeActivity(time="dayofweek", type="general", fileprefix="general", conds=conds, headers=headers)
    generateTimeActivity(time="month", type="general", fileprefix="general", conds=conds, headers=headers)

def generatePagesTimeActivity(page_id):
    page_title = pages[page_id]["page_title"] #todo namespaces
    conds = ["rev_user=0", "rev_user!=0"] #anónimo o no
    headers = ["Edits by anonymous users in %s" % page_title, "Edits by registered users in %s" % page_title]
    generateTimeActivity(time="hour", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(time="dayofweek", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(time="month", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)

def generateUsersTimeActivity(user_id):
    user_name = users[user_id]["user_name"]
    if user_name == user_id: #ip
        conds = ["rev_user_text='%s'" % user_id, "page_namespace=0 and rev_user_text='%s'" % user_id] # artículo o todas, #todo añadir escape() para comillas?
    else:
        conds = ["rev_user=%d" % user_id, "page_namespace=0 and rev_user=%d" % user_id] # artículo o todas
    headers = ["Edits by %s (all pages)" % user_name, "Edits by %s (only articles)" % user_name]
    generateTimeActivity(time="hour", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)
    generateTimeActivity(time="dayofweek", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)
    generateTimeActivity(time="month", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)

def generateCloud(type, file, conds, limit=100):
    cloud = {}
    
    conn, cursor = createConnCursor()
    for cond in conds:
        cursor.execute("SELECT rev_comment FROM %srevision" % (preferences["tablePrefix"]))
        result = cursor.fetchall()
        for row in result:
            #array('c', ) http://bytes.com/topic/python/answers/472757-mysqldb-return-strange-type-variable
            rev_comment = unicode(row[0].tostring(), "utf-8")
            line = re.sub(ur"  +", ur" ", rev_comment)
            tags = line.split(" ")
            for tag in tags:
                #unuseful tags filter
                tag = tag.lower()
                tag = re.sub(ur"[\[\]\=\,]", ur"", tag) #no commas, csv
                if len(tag)<4:
                    continue
                #end filter
                if cloud.has_key(tag):
                    cloud[tag] += 1
                else:
                    cloud[tag] = 1
    
    cloudList = []
    for tag, times in cloud.items():
       cloudList.append([times, tag])
    
    cloudList.sort()
    cloudList.reverse()
    
    header = ['word', 'frequency']
    rows = []
    c = 0
    for times, tag in cloudList:
        c+=1
        if c>limit:
            break
        rows.append([tag, str(times)])
    
    printCSV(type=type, file=file, header=header, rows=rows)
    
    destroyConnCursor(conn, cursor)

def generateGeneralCloud():
    conds = ["1"] # no condition
    generateCloud(type="general", file="general_cloud.csv", conds=conds)

def printHTML(type, file="", title="", body=""):
    if file:
        file = "%s/html/%s/%s" % (preferences["outputDir"], type, file)
    else:
        file = "%s/index.html" % (preferences["outputDir"], preferences["indexFilename"])
    
    f = open(file, "w")
    output = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es" dir="ltr">
    <header>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link rel="stylesheet" href="styles/style.css" type="text/css" media="all" />
    <title>StatMediaWiki: %s</title>
    </header>
    <body>
    <h1>StatMediaWiki: %s</h1>
    %s
    <hr/><center>Generated with <a href="http://statmediawiki.forja.rediris.es/">StatMediaWiki</a></center>
    </body>
    </html>""" % (title, title, body)
    
    f.write(output.encode("utf-8"))
    f.close()

def printLinesGraph(title, file, labels, headers, rows):
    xticsperiod=""
    c=0
    fecha=preferences["startDate"]
    fechaincremento=datetime.timedelta(days=1)
    while fecha!=preferences["endDate"]:
        if fecha.day in [1, 15]:
            xticsperiod+='"%s" %s,' % (fecha.strftime("%Y-%m-%d"), c)
        fecha+=fechaincremento
        c+=1
    xticsperiod=xticsperiod[:len(xticsperiod)-1]
    
    gp = Gnuplot.Gnuplot()
    gp('set data style lines')
    gp('set grid ytics mytics')
    #gp('set line_width 8')
    gp('set title "%s"' % title.encode("utf-8"))
    gp('set xlabel "%s"' % labels[0].encode("utf-8"))
    gp('set ylabel "%s"' % labels[1].encode("utf-8"))
    gp('set mytics 2')
    gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xticsperiod)
    plot1 = Gnuplot.PlotItems.Data(rows[0], with_="lines", title=headers[1].encode("utf-8"))
    plot2 = Gnuplot.PlotItems.Data(rows[1], with_="lines", title=headers[2].encode("utf-8"))
    gp.plot(plot1, plot2)
    gp.hardcopy(filename=file, terminal="png") 
    gp.close()

def printBarsGraph(title, file, labels, headers, rows):
    convert={}
    convert["hour"]={"0":"00", "1":"01", "2":"02", "3":"03", "4":"04", "5":"05", "6":"06", "7":"07", "8":"08", "9":"09", "10":"10", "11":"11", "12":"12", "13":"13", "14":"14", "15":"15", "16":"16", "17":"17", "18":"18", "19":"19", "20":"20", "21":"21", "22":"22", "23":"23"}
    convert["dayofweek"]={"0":"Sun", "1":"Mon", "2":"Tue", "3":"Wed", "4":"Thu", "5":"Fri", "6":"Sat"}
    convert["month"]={"0":"Jan", "1":"Feb", "2":"Mar", "3":"Apr", "4":"May", "5":"Jun", "6":"Jul", "7":"Aug", "8":"Sep", "9":"Oct", "10":"Nov", "11":"Dec"}
    convert2={"hour":"Hour", "dayofweek":"Day of week", "month":"Month"}
    xtics = ""
    for xtic in rows[0]:
        xtic_ = convert[headers[0]][str(xtic)]
        xtics += '"%s" %s, ' % (xtic_, xtic)
    xtics=xtics[:-2]
    #print xtics
    gp = Gnuplot.Gnuplot()
    gp("set style data boxes")
    gp("set grid ytics mytics")
    gp('set title "%s"' % title.encode("utf-8"))
    gp('set xlabel "%s"' % convert2[headers[0]].encode("utf-8"))
    gp('set mytics 2')
    gp('set ylabel "Edits"')
    #gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xtics.encode("utf-8"))
    plot1 = Gnuplot.PlotItems.Data(rows[1], with_="boxes", title=headers[1].encode("utf-8"))
    plot2 = Gnuplot.PlotItems.Data(rows[2], with_="boxes", title=headers[2].encode("utf-8"))
    gp.plot(plot1, plot2)
    gp.hardcopy(filename=file,terminal="png")
    gp.close()

def printGraphContentEvolution(type, fileprefix, title, headers, rows):
    labels = ["Date (YYYY-MM-DD)", "Bytes"]
    file = "%s/graphs/%s/%s_content_evolution.png" % (preferences["outputDir"], type, fileprefix)
    printLinesGraph(title=title, file=file, labels=labels, headers=headers, rows=rows)

def printGraphTimeActivity(type, fileprefix, title, headers, rows):
    labels = ["Edits", "Hour"]
    file = "%s/graphs/%s/%s_activity.png" % (preferences["outputDir"], type, fileprefix)
    printBarsGraph(title=title, file=file, labels=labels, headers=headers, rows=rows)

def generateContentEvolution(type, user_id=False, page_id=False):
    fecha=preferences["startDate"]
    fechaincremento=datetime.timedelta(days=1)
    graph1=[]
    graph2=[]
    while fecha<preferences["endDate"]:
        status={}
        statusarticles={}
        for rev_id, rev_props in revisions.items():
            if type=="general":
                pass #nos interesan todas
            elif type=="users":
                if not user_id:
                    print "Error: no hay user_id"
                if rev_props["rev_user"]!=user_id:
                    continue #nos la saltamos, no es de este usuario
            elif type=="pages":
                if not page_id:
                    print "Error: no hay page_id"
                if rev_props["rev_page"]!=page_id:
                    continue #nos la saltamos, no es de esta página
            
            if rev_props["rev_timestamp"]<fecha:
                rev_page = rev_props["rev_page"]
                #evolución de los artículos
                if pages[rev_page]["page_namespace"]==0:
                    if (statusarticles.has_key(rev_page) and statusarticles[rev_page]["rev_timestamp"]<rev_props["rev_timestamp"]) or \
                       not statusarticles.has_key(rev_page):
                        statusarticles[rev_page] = rev_props
                #evolución de todas las páginas
                if (status.has_key(rev_page) and status[rev_page]["rev_timestamp"]<rev_props["rev_timestamp"]) or \
                   not status.has_key(rev_page):
                    status[rev_page] = rev_props
    
        #recorremos entonces la instantanea de la wiki en aquel momento
        bytes=0
        for rev_page, rev_props in status.items():
            bytes+=len(rev_props["old_text"])
        graph1.append(bytes)
    
        bytesarticles=0
        for rev_page, rev_props in statusarticles.items():
            bytesarticles+=len(rev_props["old_text"])
        graph2.append(bytesarticles)
        fecha+=fechaincremento
    
    title = ""
    fileprefix = ""
    owner = ""
    if type=="general":
        title = u"Content evolution in %s" % preferences["siteName"]
        fileprefix = "general"
        owner = preferences["siteName"]
    elif type=="users":
        user_name = users[user_id]["user_name"]
        title = u"Content evolution by %s" % user_name
        fileprefix = "users_%s" % user_id
        owner = user_name
    elif type=="pages":
        page_title = pages[page_id]["page_title"]
        title = u"Content evolution in %s" % page_title
        fileprefix = "pages_%s" % page_id
        owner = page_title
    
    #falta csv
    headers = ["Date", "%s content (all pages)" % owner, "%s content (only articles)" % owner]
    headers = ["Date", "%s content (all pages)" % owner, "%s content (only articles)" % owner]
    printGraphContentEvolution(type=type, fileprefix=fileprefix, title=title, headers=headers, rows=[graph1, graph2])

def generateGeneralContentEvolution():
    generateContentEvolution(type="general")
    
def generateUsersContentEvolution(user_id):
    generateContentEvolution(type="users", user_id=user_id)
    
def generatePagesContentEvolution(page_id):
    generateContentEvolution(type="pages", page_id=page_id)

def generateUsersTable():
    output = u"""<table>
    <tr><th>#</th><th>User</th><th>Edits</th><th>Edits in articles</th><th>Bytes added</th><th>Bytes added in articles</th><th>Uploads</th></tr>"""
    
    sortedUsers = [] #by edits
    for user_id, user_props in users.items():
        sortedUsers.append([len(user_props["revisions"]), user_id])
    sortedUsers.sort()
    sortedUsers.reverse()
    
    c=1
    for revisionsNumber, user_id in sortedUsers:
        user_props = users[user_id]
        editsInAllPages = len(user_props["revisions"])
        editsInArticles = 0
        for rev_id, rev_props in revisions.items():
            rev_page = rev_props["rev_page"]
            if pages[rev_page]["page_namespace"] == 0:
                editsInArticles += 1
        output += u"""<tr><td>%s</td><td><a href="html/users/user_%s.html">%s</a></td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s</td></tr>\n""" % (c, user_id, user_props["user_name"], editsInAllPages, 0, 0, 0, 0, 0, 0, 0, 0)
        c+=1
    
    output += """</table>"""
    
    return output

def generateGeneralAnalysis():
    print "Generando análisis general"
    conn, cursor = createConnCursor()
    
    dict = {}
    
    cursor.execute("SELECT COUNT(user_id) AS count FROM %suser WHERE 1" % preferences["tablePrefix"])
    dict["totalusers"] = cursor.fetchall()[0][0]
    
    #número de usuarios a partir de las revisiones y de la tabla de usuarios, len(user.items())
    cursor.execute("SELECT COUNT(rev_id) AS count FROM %srevision WHERE 1" % preferences["tablePrefix"])
    dict["totaledits"] = cursor.fetchall()[0][0]
    
    #todo: con un inner join mejor?
    cursor.execute("SELECT COUNT(rev_id) AS count FROM %srevision WHERE rev_page IN (SELECT page_id FROM %spage WHERE page_namespace=0)" % (preferences["tablePrefix"], preferences["tablePrefix"]))
    dict["totaleditsinarticles"] = cursor.fetchall()[0][0]
    
    cursor.execute("SELECT COUNT(page_id) AS count FROM %spage WHERE 1" % preferences["tablePrefix"])
    dict["totalpages"] = cursor.fetchall()[0][0]
    
    cursor.execute("SELECT COUNT(*) AS count FROM %spage WHERE page_namespace=0 AND page_is_redirect=0" % preferences["tablePrefix"])
    dict["totalarticles"] = cursor.fetchall()[0][0]
    
    cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE 1" % preferences["tablePrefix"])
    dict["totalbytes"] = cursor.fetchall()[0][0]
    
    cursor.execute("SELECT SUM(page_len) AS count FROM %spage WHERE page_namespace=0 AND page_is_redirect=0" % preferences["tablePrefix"])
    dict["totalbytesinarticles"] = cursor.fetchall()[0][0]
    
    cursor.execute("SELECT COUNT(*) AS count FROM %simage WHERE 1" % preferences["tablePrefix"])
    dict["totalfiles"] = cursor.fetchall()[0][0]
    dateGenerated = datetime.datetime.now().isoformat()
    period = "%s &ndash %s" % (preferences["startDate"].isoformat(), preferences["endDate"].isoformat())
    
    body = u"""<dl>
    <dt>Site:</dt>
    <dd><a href='%s'>%s</a></dd>
    <dt>Generated:</dt>
    <dd>%s</dt>
    <dt>Report period:</dt>
    <dd>%s</dd>
    <dt>Total pages:</dt>
    <dd>%s (Articles: %s)</dd>
    <dt>Total edits:</dt>
    <dd>%s (In articles: %s)</dd>
    <dt>Total bytes:</dt>
    <dd>%s (In articles: %s)</dd>
    <dt>Total files:</dt>
    <dd><a href="%s%s/Special:Imagelist">%s</a></dd>
    <dt>Users:</dt>
    <dd><a href="users.html">%s</a></dd>
    </dl>
    <h2>Content evolution</h2>
    <center>
    <img src="graphs/general/general_content_evolution.png" />
    </center>
    <h2>Activity</h2>
    <center>
    <img src="graphs/general/general_hour_activity.png" />
    <img src="graphs/general/general_dayofweek_activity.png" />
    <img src="graphs/general/general_month_activity.png" />
    </center>
    <h2>Users</h2>
    <center>
    %s
    </center>
    <h2>Pages</h2>
    </center>
    </center>
    <h2>Tags cloud</h2>
    <center>
    </center>
    """ % (preferences["siteUrl"], preferences["siteName"], 0, 0, dict["totalpages"], dict["totalarticles"], dict["totaledits"], dict["totaleditsinarticles"], dict["totalbytes"], dict["totalbytesinarticles"], preferences["siteUrl"], preferences["subDir"], dict["totalfiles"], dict["totalusers"], generateUsersTable())
    
    generateGeneralContentEvolution()
    generateGeneralTimeActivity()
    #generateGeneralCloud()
    
    printHTML(type="general", title=preferences["siteName"], body=body)
    
    destroyConnCursor(conn, cursor)

def generatePagesAnalysis():
    for page_id, page_props in pages.items():
        print u"Generando análisis para la página %s" % pages[page_id]["page_title"]
        generatePagesContentEvolution(page_id=page_id)
        generatePagesTimeActivity(page_id=page_id)

def generateUsersAnalysis():
    for user_id, user_props in users.items():
        user_name = user_props["user_name"]
        print u"Generando análisis para el usuario %s" % user_name
        generateUsersContentEvolution(user_id=user_id)
        generateUsersTimeActivity(user_id=user_id)
        
        body = u"""<dl>
        <dt>User:</dt>
        <dd><a href='%s/%s/User:%s'>%s</a></dd>
        </dl>
        <h2>Content evolution by %s</h2>
        <center>
        <img src="graphs/%s/user_%s__content_evolution.png" />
        </center>
        <h2>Activity by %s</h2>
        <center>
        <img src="graphs/%s/user_%s_hour_activity.png" />
        <img src="graphs/%s/user_%s_dayofweek_activity.png" />
        <img src="graphs/%s/user_%s_month_activity.png" />
        </center>
        <h2>Tags cloud</h2>
        <center>
        </center>
        """ % (preferences["siteUrl"], preferences["subDir"], user_name, user_name, user_name, user_id, user_name, user_id, user_id, user_id)
        
        title = "%s: User:%s" % (preferences["siteName"], user_name)
        printHTML(type="users", file="user_%s.html" % user_id, title=title, body=body)

def generateAnalysis():
    generateGeneralAnalysis()
    generatePagesAnalysis()
    generateUsersAnalysis()

def bye():
    print "StatMediaWiki has finished correctly. Killing process to exit program."
    os.system("kill -9 %s" % os.getpid())

def main():
    welcome()
    
    getParameters()
    loadPages()
    loadImages()
    loadRevisions()
    loadUsers() #revisions and uploads loaded required
    initialize() #dbname required
    manageOutputDir()
    generateAnalysis()
    copyFiles()
    
    bye()

if __name__ == "__main__":
    main()


