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
import md5
#import hashlib #From python2.5
import MySQLdb
import os
import re
import time
import shutil
import sys

from statmediawiki_globals import *

global preferences
global user_ids
user_ids = {}
global page_ids
page_ids = {}

#todo:
#con que numero se lanzan los sys.exit() cuando hay un fallo?
#que las rutas ../../ no sean relativas, buscar algo como $IP o __file__ ?

#el usuario que hace las consultas sql debe tener acceso lectura a las bbdd, con los datos de .my.cnf
t1=time.time()

def initialize():
    conn, cursor = createConnCursor()
    
    cursor.execute("SELECT rev_timestamp FROM %srevision ORDER BY rev_timestamp DESC LIMIT 1" % (preferences["tablePrefix"]))
    a = cursor.fetchall()[0][0]
    preferences["startDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=0, minute=0, second=0)
    
    cursor.execute("SELECT rev_timestamp FROM %srevision ORDER BY rev_timestamp ASC LIMIT 1" % (preferences["tablePrefix"]))
    a = cursor.fetchall()[0][0]
    preferences["endDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=0, minute=0, second=0)
    
    destroyConnCursor(conn, cursor)

def loadUserIds():
    global user_ids
    
    conn, cursor = createConnCursor()
    cursor.execute("SELECT user_id, user_name FROM %suser" % (preferences["tablePrefix"]))
    result = cursor.fetchall()
    user_ids = {}
    for user_id, user_name in result:
        user_ids[user_id] = user_name
    
    destroyConnCursor(conn, cursor)

def loadPageIds():
    global page_ids
    
    conn, cursor = createConnCursor()
    cursor.execute("SELECT page_id, page_title FROM %spage" % (preferences["tablePrefix"]))
    result = cursor.fetchall()
    page_ids = {}
    for page_id, page_title in result:
        page_ids[page_id] = page_title
    
    destroyConnCursor(conn, cursor)

def welcome():
    pass

def usage():
    f=open("help.txt", "r")
    print f.read()
    f.close()
    sys.exit() #mostramos ayuda y salimos

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

def getParameters():
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
        "%s/dependences" % preferences["outputDir"],
        "%s/dependences/pChart" % preferences["outputDir"],
        "%s/dependences/pChart/pChart" % preferences["outputDir"],
        "%s/dependences/pChart/Fonts" % preferences["outputDir"],
        "%s/php" % preferences["outputDir"],
        "%s/php/generators" % preferences["outputDir"],
        "%s/php/generators/general" % preferences["outputDir"],
        "%s/php/generators/pages" % preferences["outputDir"],
        "%s/php/generators/users" % preferences["outputDir"],
        "%s/php/styles" % preferences["outputDir"],
    ]
    for directory in directories:
        if not os.path.exists(directory) or not os.path.isdir(directory):
            try:
                os.makedirs(directory)
                print "Creando %s" % directory
            except:
                print "Hubo un error al intentar crear la ruta %s" % directory
                sys.exit()

def copyPHPFiles():
    #Copiando ficheros individuales
    #Van en el nivel principal (están duplicados con la línea anterior)
    shutil.copyfile("%s/php/index.php" % (preferences["currentPath"]), "%s/index.php" % (preferences["outputDir"]))
    shutil.copyfile("%s/php/functions.php" % (preferences["currentPath"]), "%s/php/functions.php" % (preferences["outputDir"]))
    os.system("cp %s/php/generators/*.php %s/php/generators" % (preferences["currentPath"], preferences["outputDir"]))
    os.system("cp %s/php/generators/general/*.php %s/php/generators/general" % (preferences["currentPath"], preferences["outputDir"]))
    os.system("cp %s/php/generators/pages/*.php %s/php/generators/pages" % (preferences["currentPath"], preferences["outputDir"]))
    os.system("cp %s/php/generators/users/*.php %s/php/generators/users" % (preferences["currentPath"], preferences["outputDir"]))
    os.system("cp %s/php/styles/*.css %s/php/styles" % (preferences["currentPath"], preferences["outputDir"]))
    os.system("cp %s/dependences/pChart/pChart/*.class %s/dependences/pChart/pChart" % (preferences["currentPath"], preferences["outputDir"]))
    os.system("cp %s/dependences/pChart/Fonts/*.ttf %s/dependences/pChart/Fonts" % (preferences["currentPath"], preferences["outputDir"]))
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

def generateGeneralAnalysis():
    conn, cursor = createConnCursor()
    
    dict = {}
    dict["sitename"] = preferences["siteName"]
    dict["siteurl"] = preferences["siteUrl"]
    
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
    
    keysList = []
    valuesList = []
    for k, v in dict.items():
        keysList.append(k)
        valuesList.append(str(v))
    
    printCSV(type="general", file="general.csv", header=keysList, rows=[valuesList])
    
    generateGeneralAnalysisTimeActivity()
    generateGeneralCloud()
    
    destroyConnCursor(conn, cursor)

def generatePagesAnalysis():
    pass

def generateUsersAnalysis():
    generateUsersAnalysisHourActivity()

def generateAnalysis():
    generateGeneralAnalysis()
    generatePagesAnalysis()
    generateUsersAnalysis()

def bye():
    pass

def main():
    welcome()
    
    getParameters()
    loadUserIds()
    loadPageIds()
    initialize() #dbname required
    manageOutputDir()
    generateAnalysis()
    copyPHPFiles()
    
    bye()

if __name__ == "__main__":
    main()


