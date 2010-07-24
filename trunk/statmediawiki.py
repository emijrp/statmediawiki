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

def loadUsers():
    global users
    
    conn, cursor = createConnCursor()
    cursor.execute("SELECT user_id, user_name FROM %suser" % (preferences["tablePrefix"]))
    result = cursor.fetchall()
    users = {}
    for row in result:
        users[row[0]] = {"user_name" : unicode(row[1], "utf-8")}
    print "Loaded %s users" % len(users.items())
    
    destroyConnCursor(conn, cursor)

def loadPages():
    global pages
    
    conn, cursor = createConnCursor()
    cursor.execute("select page_id, page_namespace, page_title, page_is_redirect from %spage" % preferences["tablePrefix"])
    result = cursor.fetchall()
    pages = {}
    for row in result:
        pages[row[0]]={"page_namespace": int(row[1]), "page_title": unicode(row[2], "utf-8"), "page_is_redirect": int(row[3])}
    print "Loaded %s pages" % len(pages.items())
    
    destroyConnCursor(conn, cursor)

def loadRevisions():
    global revisions
    
    conn, cursor = createConnCursor()
    cursor.execute("select rev_id, rev_page, rev_user_text, rev_timestamp, rev_comment, old_text from %srevision, %stext where old_id=rev_text_id and rev_timestamp>='%s' and rev_timestamp<='%s'" % (preferences["tablePrefix"], preferences["tablePrefix"], '%sZ000000T' % re.sub('-', '', preferences["startDate"].isoformat().split("T")[0]), '%sZ235959T' % re.sub('-', '', preferences["endDate"].isoformat().split("T")[0])))
    result=cursor.fetchall()
    for row in result:
        revisions[row[0]]={"rev_id": row[0], "rev_page":row[1], "rev_user_text": unicode(row[2], "utf-8"), 
    "rev_timestamp": datetime.datetime(year=int(row[3][:4]), month=int(row[3][4:6]), day=int(row[3][6:8]), hour=int(row[3][8:10]), minute=int(row[3][10:12]), second=int(row[3][12:14])), "rev_comment": unicode(row[4].tostring(), "utf-8"), "old_text": unicode(row[5].tostring(), "utf-8")} #el rev_id no es un error
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

def generateAnalysisTimeActivity(time, type, file, conds, headers):
    results = {}
    
    conn, cursor = createConnCursor()
    for cond in conds:
        cursor.execute("SELECT %s(rev_timestamp) AS time, COUNT(rev_id) AS count FROM %srevision INNER JOIN %spage ON rev_page=page_id WHERE %s GROUP BY time ORDER BY time" % (time, preferences["tablePrefix"], preferences["tablePrefix"], cond))
        result = cursor.fetchall()
        results[cond] = {}
        for hour, edits in result:
            results[cond][str(hour)] = str(edits)
    
    header = [time] + headers
    rows = []
    if time == "hour":
        range_ = range(24)
    elif time == "dayofweek":
        range_ = range(1,8)
    elif time == "month":
        range_ = range(1,13)
    
    for period in range_:
        period  = str(period)
        cond0 = "0"
        cond1 = "0"
        if results[conds[0]].has_key(period):
            cond0 = results[conds[0]][period]
        
        if results[conds[1]].has_key(period):
            cond1 = results[conds[1]][period]
        rows.append([period, cond0, cond1])
    
    printCSV(type=type, file=file, header=header, rows=rows)
    printGraphTimeActivity(type=type, file=file, headers=headers, rows=rows)
    
    destroyConnCursor(conn, cursor)

def generateAnalysisHourActivity(type, file, conds, headers):
    generateAnalysisTimeActivity(time="hour", type=type, file=file, conds=conds, headers=headers)

def generateAnalysisDayOfWeekActivity(type, file, conds, headers):
    generateAnalysisTimeActivity(time="dayofweek", type=type, file=file, conds=conds, headers=headers)

def generateAnalysisMonthActivity(type, file, conds, headers):
    generateAnalysisTimeActivity(time="month", type=type, file=file, conds=conds, headers=headers)

def generateGeneralAnalysisTimeActivity():
    conds = ["page_namespace=0", "page_namespace!=0"] # artículo o no
    headers = ["edits in articles", "rest of edits"]
    generateAnalysisHourActivity(type="general", file="general_hour_activity.csv", conds=conds, headers=headers)
    generateAnalysisDayOfWeekActivity(type="general", file="general_dayofweek_activity.csv", conds=conds, headers=headers)
    generateAnalysisMonthActivity(type="general", file="general_month_activity.csv", conds=conds, headers=headers)

def generatePagesAnalysisHourActivity():
    for page_id in page_ids:
        conds = ["rev_user=0", "rev_user!=0"] #anónimo o no
        headers = ["edits by anons", "edits by registered users"]
        generateAnalysisHourActivity(type="pages", file="page_%d_hour_activity.csv" % page_id, conds=conds, headers=headers)

def generateUsersAnalysisHourActivity():
    for user_id in user_ids:
        conds = ["page_namespace=0 and rev_user=%d" % user_id, "page_namespace!=0 and rev_user=%d" % user_id] # artículo o no
        headers = ["edits in articles", "rest of edits"]
        generateAnalysisHourActivity(type="users", file="user_%d_hour_activity.csv" % user_id, conds=conds, headers=headers)

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

def printHTML(type, file, title="", body=""):
    f = open("%s/%s" % (preferences["outputDir"], file), "w")
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
    #gp('set size .6, .6')
    #gp('set line_width 8')
    gp('set title "%s"' % title)
    gp('set xlabel "%s"' % labels[0])
    gp('set ylabel "%s"' % labels[1])
    gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xticsperiod)
    plot1 = Gnuplot.PlotItems.Data(rows[0], with_="lines", title=headers[1])
    plot2 = Gnuplot.PlotItems.Data(rows[1], with_="lines", title=headers[2])
    gp.plot(plot1, plot2)
    gp.hardcopy(filename=file, terminal="png") 
    gp.close()

def printBarsGraph(title, file, labels, headers, rows):
    xtics24hours='"00" 0, "01" 1, "02" 2, "03" 3, "04" 4, "05" 5, "06" 6, "07" 7, "08" 8, "09" 9, "10" 10, "11" 11, "12" 12, "13" 13, "14" 14, "15" 15, "16" 16, "17" 17, "18" 18, "19" 19, "20" 20, "21" 21, "22" 22, "23" 23'
    gp = Gnuplot.Gnuplot()
    gp("set data style boxes")
    gp('set title "Hour activity"')
    gp('set xlabel "Hour"')
    gp('set ylabel "Edits"')
    gp('set xtics (%s)' % xtics24hours)
    plottitle1=u"Edits"
    plot1 = Gnuplot.PlotItems.Data(houractivity_list, with_="boxes", title=plottitle1.encode("utf-8"))
    gp.plot(plot1)
    gp.hardcopy(filename=file,terminal="png")
    gp.close()

def printGraphContentEvolution(type, file, headers, rows):
    labels = ["Date", "Bytes"]
    if type=="general":
        printLinesGraph(title="Content evolution in %s" % preferences["siteName"], file="%s/graphs/%s/%s" % (preferences["outputDir"], type, file), labels=labels, headers=headers, rows=rows)

def printGraphTimeActivity(type, file, headers, rows):
    labels = ["Edits", "Hour"]
    if type=="general":
        printBarsGraph(title="Activity per %s" % header[0], file="%s/graphs/%s/%s" % (preferences["outputDir"], type, file), labels=labels, headers=headers, rows=rows)

def generateGeneralContentEvolution():
    fecha=preferences["startDate"]
    fechaincremento=datetime.timedelta(days=1)
    graph1=[]
    graph2=[]
    c=0
    while fecha<preferences["endDate"]:
        status={}
        statusarticles={}
        for rev_id, rev_props in revisions.items():
            if rev_props["rev_timestamp"]<fecha and ((status.has_key(rev_props["rev_page"]) and status[rev_props["rev_page"]]["rev_timestamp"]<rev_props["rev_timestamp"]) or not status.has_key(rev_props["rev_page"])):
                status[rev_props["rev_page"]]=rev_props
    
        for rev_id, rev_props in revisions.items():
            if pages[rev_props["rev_page"]]["page_namespace"]==0 and rev_props["rev_timestamp"]<fecha and ((statusarticles.has_key(rev_props["rev_page"]) and statusarticles[rev_props["rev_page"]]["rev_timestamp"]<rev_props["rev_timestamp"]) or not statusarticles.has_key(rev_props["rev_page"])):
                statusarticles[rev_props["rev_page"]]=rev_props
    
        #recorremos entonces la instantanea de la wiki en aquel momento
        bytes=0
        for rev_page, rev_props in status.items():
            bytes+=len(rev_props["old_text"])
        graph1.append([c, bytes])
    
        bytesarticles=0
        for rev_page, rev_props in statusarticles.items():
            bytesarticles+=len(rev_props["old_text"])
        graph2.append([c, bytesarticles])
        c+=1
        fecha+=fechaincremento
    
    
    #print csv todo
    printGraphContentEvolution(type="general", file="general_content_evolution.png", headers=["Date", "%s content (only articles)" % preferences["siteName"], "%s content (all pages)" % preferences["siteName"]], rows=[graph1, graph2])
    
def generateGeneralAnalysis():
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
    <img src="graphs/general/general_content_evolution.png" />
    <h2>Activity</h2>
    <img src="graphs/general/general_hour_activity.png" />
    <img src="graphs/general/general_dayofweek_activity.png" />
    <img src="graphs/general/general_month_activity.png" />
    <h2>Users</h2>
    <h2>Pages</h2>
    <h2>Tags cloud</h2>
    """ % (preferences["siteUrl"], preferences["siteName"], 0, 0, dict["totalpages"], dict["totalarticles"], dict["totaledits"], dict["totaleditsinarticles"], dict["totalbytes"], dict["totalbytesinarticles"], preferences["siteUrl"], preferences["subDir"], dict["totalfiles"], dict["totalusers"])
    
    #generateGeneralContentEvolution()
    #generateGeneralAnalysisTimeActivity()
    #generateGeneralCloud()
    
    printHTML(type="general", file=preferences["indexFilename"], title=preferences["siteName"], body=body)
    
    destroyConnCursor(conn, cursor)

def generatePagesAnalysis():
    pass

def generateUsersAnalysis():
    pass
    #generateUsersAnalysisHourActivity()

def generateAnalysis():
    generateGeneralAnalysis()
    #generatePagesAnalysis()
    #generateUsersAnalysis()

def bye():
    print "StatMediaWiki has finished correctly. Killing process to exit program."
    os.system("kill -9 %s" % os.getpid())

def main():
    welcome()
    
    getParameters()
    loadUsers()
    loadPages()
    loadRevisions()
    initialize() #dbname required
    manageOutputDir()
    generateAnalysis()
    copyFiles()
    
    bye()

if __name__ == "__main__":
    main()


