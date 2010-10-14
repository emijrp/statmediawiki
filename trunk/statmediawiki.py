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
import getopt
import Gnuplot
import md5
#import hashlib #From python2.5
import MySQLdb
import os
import random
import re
import time
import shutil
import sys

#data
images = {}
pages = {}
categories = {}
preferences = {}
users = {}
revisions = {}
namespaces = {-2: u"Media", -1: u"Special", 0: "Main", 1: u"Talk", 2: u"User", 3: u"User talk", 4: u"Project", 5: u"Project talk", 6: u"File", 7: u"File talk", 8: u"MediaWiki", 9: u"MediaWiki talk", 10: u"Template", 11: u"Template talk", 12: u"Help", 13: u"Help talk", 14: u"Category", 15: u"Category talk"}

#user preferences
preferences["outputDir"] = "output"
preferences["indexFilename"] = "index.html"
preferences["siteName"] = ""
preferences["siteUrl"] = ""
preferences["subDir"] = "index.php" #MediaWiki subdir, usually "index.php" in http://osl.uca.es/wikihaskell/index.php/Main_Page
preferences["dbName"] = ""
preferences["tablePrefix"] = "" #Usually empty
preferences["startDate"] = "" #auto, start point for date range
preferences["endDate"] = "" #auto, end point for date range
preferences["currentPath"] = os.path.dirname(__file__)
preferences["anonymous"] = False

#todo:
#con que numero se lanzan los sys.exit() cuando hay un fallo?
#que las rutas ../../ no sean relativas, buscar algo como $IP o __file__ ?
#len() devuelve bytes?

#conv:
#convenciones:
#solo contamos los añadidos de texto, no cuando se elimina texto (no se penaliza a nadie)

#el usuario que hace las consultas sql debe tener acceso lectura a las bbdd, con los datos de .my.cnf
t1=time.time()

def createConnCursor():
    conn = MySQLdb.connect(db=preferences["dbName"], read_default_file='~/.my.cnf', use_unicode=False) #pedir ruta absoluta del fichero cnf? #todo
    cursor = conn.cursor()
    try:
        conn = MySQLdb.connect(db=preferences["dbName"], read_default_file='~/.my.cnf', use_unicode=False) #pedir ruta absoluta del fichero cnf? #todo
        cursor = conn.cursor()
    except:
        print "Hubo un error al conectarse a la base de datos"
        sys.exit()
    return conn, cursor

def destroyConnCursor(conn, cursor):
    cursor.close()
    conn.close()

def getImageUrl(img_name):
    img_name_ = re.sub(' ', '_', img_name) #espacios a _
    md5_ = md5.md5(img_name_.encode('utf-8')).hexdigest() #digest hexadecimal
    img_url = u"%s/images/%s/%s/%s" % (preferences["siteUrl"], md5_[0], md5_[:2], img_name_)
    return img_url

def getUserImages(user_id):
    user_images = []
    for img_name, imageprops in images.items():
        if imageprops["img_user"] == user_id:
            user_images.append(img_name)
    return user_images

def noise(s):
    s = u"%s%s%s" % (random.randint(1, 999999999), s, random.randint(1, 999999999))
    s = md5.new(s.encode('utf-8')).hexdigest()
    return s

def anonimize():
    #tables & dicts with user information:
    #* images: img_user, img_user_text
    #* users: key, user_name
    #* revisions: rev_user, rev_user_text
    #* pages: nothing
    #
    global images
    global revisions
    global users

    users_ = {}
    anonymous_table = {}
    #create anonymous table which is destroyed after exit this function
    #anonimyze users dict
    for user_id, user_props in users.items():
        user_name = user_props["user_name"]
        user_id_ = noise(str(user_id))
        user_name_ = noise(user_name)
        while user_id_ in anonymous_table.values() or user_name_ in anonymous_table.values():
            user_id_ = noise(str(user_id))
            user_name_ = noise(user_name)
        anonymous_table[str(user_id)] = user_id_
        anonymous_table[user_name] = user_name_

        user_props_ = user_props
        user_props_["user_name"] = user_name_

        users_[user_id_] = user_props_
    users = users_

    #anonimize images dict
    for img_name, img_props in images.items():
        img_props_ = img_props
        img_props_["img_user"] = anonymous_table[str(img_props_["img_user"])]
        img_props_["img_user_text"] = anonymous_table[img_props_["img_user_text"]]
        images[img_name] = img_props_

    #anonimize revisions dict
    for rev_id, rev_props in revisions.items():
        rev_props_ = rev_props
        rev_props_["rev_user"] = anonymous_table[str(rev_props_["rev_user"])]
        rev_props_["rev_user_text"] = anonymous_table[rev_props_["rev_user_text"]]
        revisions[rev_id] = rev_props_

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
        if img_user == 0: #ip (no es normal que la subida anónima esté habilitada, pero quien sabe...)
            img_user = img_user_text
        img_timestamp = row[3]
        img_size = int(row[4])
        images[img_name] = {
            "img_user": img_user,
            "img_user_text": img_user_text,
            "img_timestamp": img_timestamp,
            "img_size": img_size,
            "img_url": getImageUrl(img_name),
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
            if not users.has_key(user_id):
                users[user_id] = {
                    "user_name": user_name,
                    "images": [],
                    "revisions": [],
                    "revisionsbynamespace": {"*": 0, 0: 0},
                    "bytesbynamespace": {"*": 0, 0: 0},
                }
    print "Loaded %s users" % len(users.items())

    #cargamos listas de images y revisiones para cada usuario
    #no puede hacerse en el bucle anterior porque getUserImages() y la otra función, llaman a users y necesitan que users esté relleno ya
    for user_id, user_props in users.items():
        users[user_id]["images"] = getUserImages(user_id)
        users[user_id]["revisions"] = getUserRevisions(user_id)

    #revisions by namespace
    for rev_id, rev_props in revisions.items():
        rev_page = rev_props["rev_page"]
        rev_user = rev_props["rev_user"]
        users[rev_user]["revisionsbynamespace"]["*"] += 1
        if pages[rev_page]["page_namespace"] == 0:
            users[rev_user]["revisionsbynamespace"][0] += 1

    destroyConnCursor(conn, cursor)

def loadPages():
    global pages
    pages = {}

    conn, cursor = createConnCursor()
    cursor.execute("select page_id, page_namespace, page_title, page_is_redirect, page_len, page_counter from %spage" % preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        page_id = int(row[0])
        page_namespace = int(row[1])
        page_title = unicode(re.sub("_", " ", row[2]), "utf-8")
        if page_namespace != 0:
            page_title = u"%s:%s" % (namespaces[page_namespace], page_title)
        page_is_redirect = int(row[3])
        page_len = int(row[4])
        page_counter = int(row[5])
        pages[page_id] = {
            "page_namespace": page_namespace,
            "page_title": page_title,
            "page_is_redirect": page_is_redirect,
            "page_len": page_len,
            "page_counter": page_counter, #visits
            "revisions": [],
            "revisionsbyuserclass": {"anon": 0, "reg": 0},
            "edits": 0,
        }
    print "Loaded %s pages" % len(pages.items())

    #count edits per page
    for rev_id, rev_props in revisions.items():
        rev_page = rev_props["rev_page"]
        if pages.has_key(rev_page):
            pages[rev_page]["edits"] += 1
            pages[rev_page]["revisions"].append(rev_id)
            if rev_props["rev_user"] == rev_props["rev_user_text"]: #anon #todo:  tener una variable is_anon en cada revisión?
                pages[rev_page]["revisionsbyuserclass"]["anon"] += 1
            else:
                pages[rev_page]["revisionsbyuserclass"]["reg"] += 1
        else:
            print "Page", rev_page, "not found"
            sys.exit()

    destroyConnCursor(conn, cursor)

def loadCategories():
    global categories
    categories = {}

    conn, cursor = createConnCursor()
    #capturamos el cl_to que es el título de la categoría, en vez de su ID, porque puede haber categorylinks hacia categorías cuya página no existe
    cursor.execute("select cl_from, cl_to from %scategorylinks where 1" % preferences["tablePrefix"])
    result = cursor.fetchall()
    for row in result:
        cl_from = int(row[0])
        cl_to = unicode(re.sub("_", " ", row[1]), "utf-8")

        if categories.has_key(cl_to):
            categories[cl_to].append(cl_from)
        else:
            categories[cl_to] = [cl_from]
    print "Loaded %s categories" % len(categories.items())

    destroyConnCursor(conn, cursor)

def loadRevisions():
    global revisions

    conn, cursor = createConnCursor()
    cursor.execute("select rev_id, rev_page, rev_user, rev_user_text, rev_timestamp, rev_comment, rev_parent_id, old_text from %srevision, %stext where old_id=rev_text_id" % (preferences["tablePrefix"], preferences["tablePrefix"]))
    result = cursor.fetchall()
    for row in result:
        rev_id = int(row[0])
        rev_page = int(row[1])
        rev_user = int(row[2])
        rev_user_text = unicode(re.sub("_", " ", row[3]), "utf-8")
        if rev_user == 0: #ip
            rev_user = rev_user_text
        rev_timestamp = row[4]
        rev_comment = unicode(row[5].tostring(), "utf-8")
        rev_parent_id = int(row[6])
        old_text = unicode(row[7].tostring(), "utf-8")
        revisions[rev_id] = {
            "rev_id": rev_id, #no es un error
            "rev_page": rev_page,
            "rev_user": rev_user,
            "rev_user_text": rev_user_text,
            "rev_timestamp": datetime.datetime(year=int(rev_timestamp[:4]), month=int(rev_timestamp[4:6]), day=int(rev_timestamp[6:8]), hour=int(rev_timestamp[8:10]), minute=int(rev_timestamp[10:12]), second=int(rev_timestamp[12:14])),
            "rev_comment": rev_comment,
            "rev_parent_id": rev_parent_id,
            "old_text": old_text,
            "len_diff": 0,
        }
    print "Loaded %s revisions" % len(revisions.items())

    #len_diff, incremento de tamaño respecto a la versión anterior (si es negativo es decremento)
    for rev_id, rev_props in revisions.items():
        #que pasa con los rev_parent_id que apuntan a revisiones borradas?
        rev_parent_id = rev_props["rev_parent_id"]
        if rev_parent_id == 0: #es la primera revisión de esta página
            revisions[rev_id]["len_diff"] = len(rev_props["old_text"])
        elif revisions.has_key(rev_parent_id):
            revisions[rev_id]["len_diff"] = len(rev_props["old_text"]) - len(revisions[rev_parent_id]["old_text"])
        else:
            print "Revision", rev_parent_id, "not found"
            sys.exit()

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
        preferences["endDate"] = datetime.datetime(year=int(a[:4]), month=int(a[4:6]), day=int(a[6:8]), hour=23, minute=59, second=59)

    destroyConnCursor(conn, cursor)

def welcome():
    print "-"*75
    print u"""Welcome to StatMediaWiki 1.0. Web: http://statmediawiki.forja.rediris.es"""
    print "-"*75

def usage():
    filename = "help.txt"
    if preferences["currentPath"]:
        filename = "%s/%s" % (preferences["currentPath"], filename)
    f=open(filename, "r")
    print f.read()
    f.close()
    sys.exit() #mostramos ayuda y salimos

def getParameters():
    global preferences

    #console params
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["h", "help", "anonymous", "outputdir=", "index=", "sitename=", "subdir=", "siteurl=", "dbname=", "tableprefix=", "startdate=", "enddate="])
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
        elif o in ("--anonymous"):
            preferences["anonymous"] = True
        else:
            assert False, "unhandled option"

    #gestionar falta de parametros
    if not preferences["dbName"] or \
       not preferences["siteUrl"] or \
       not preferences["siteName"]:
        print u"""Error. Parameters --dbname, --siteurl and --sitename are required. Write --help for help."""
        sys.exit()
        #usage()

    #fin gestionar falta parametros

def manageOutputDir():
    #Generando estructura de directorios
    directories = [
        preferences["outputDir"],
        "%s/csv" % preferences["outputDir"],
        "%s/csv/general" % preferences["outputDir"],
        "%s/csv/users" % preferences["outputDir"],
        "%s/csv/pages" % preferences["outputDir"],
        "%s/csv/categories" % preferences["outputDir"],
        "%s/graphs" % preferences["outputDir"],
        "%s/graphs/general" % preferences["outputDir"],
        "%s/graphs/users" % preferences["outputDir"],
        "%s/graphs/pages" % preferences["outputDir"],
        "%s/graphs/categories" % preferences["outputDir"],
        "%s/html" % preferences["outputDir"],
        "%s/html/general" % preferences["outputDir"],
        "%s/html/users" % preferences["outputDir"],
        "%s/html/pages" % preferences["outputDir"],
        "%s/html/categories" % preferences["outputDir"],
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

# Generamos una columna virtual con fechas a partir de una fecha
# determinada, con un salto determinado entre elementos (por omision,
# un dia)
def generadorColumnaFechas(startDate, delta=datetime.timedelta(days=1)):
    currentDate = startDate
    while True:
        yield currentDate
        currentDate += delta

def printCSV(type, subtype, fileprefix, headers, rows):
    # Type puede ser: general, users o pages
    file = "%s/csv/%s/%s_%s.csv" % (preferences["outputDir"], type,
                                    fileprefix, subtype)
    f = open(file, "w")
    output = ",".join(headers)
    output += "\n"
    f.write(output.encode("utf-8"))

    # Cada "fila" tiene los datos de una columna, en realidad. Con
    # zip() hacemos la transpuesta de la matriz e imprimimos el CSV
    # correctamente.
    for row in zip(*rows):
        output = ",".join(str(e) for e in row) + "\n"
        f.write(output.encode("utf-8"))
    f.close()

def generateTimeActivity(time, type, fileprefix, conds, headers, user_id=None, page_id=None):
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

    # Print rows
    printCSV(type=type, subtype="activity", fileprefix=fileprefix,
             headers=headers, rows=rows)
    printGraphTimeActivity(type=type, fileprefix=fileprefix, title=title,
                           headers=headers, rows=rows)

    destroyConnCursor(conn, cursor)

def generateGeneralTimeActivity():
    conds = ["1", "page_namespace=0", "page_namespace=1"] # artículo o todas
    headers = ["Edits (all pages)", "Edits (only articles)", "Edits (only articles talks)"]
    generateTimeActivity(time="hour", type="general", fileprefix="general", conds=conds, headers=headers)
    generateTimeActivity(time="dayofweek", type="general", fileprefix="general", conds=conds, headers=headers)
    generateTimeActivity(time="month", type="general", fileprefix="general", conds=conds, headers=headers)

def generatePagesTimeActivity(page_id):
    page_title = pages[page_id]["page_title"] #todo namespaces
    conds = ["1", "rev_user=0", "rev_user!=0"] #todas, anónimas o registrados
    headers = ["Edits in %s (all users)" % page_title, "Edits in %s (only anonymous users)" % page_title, "Edits in %s (only registered users)" % page_title]
    generateTimeActivity(time="hour", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(time="dayofweek", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(time="month", type="pages", fileprefix="page_%d" % page_id, conds=conds, headers=headers, page_id=page_id)

def generateCategoriesTimeActivity(page_id):
    category_title = ':'.join(pages[page_id]["page_title"].split(':')[1:]) #todo namespaces
    conds2 = ["1", "rev_user=0", "rev_user!=0"] #todas, anónimas o registrados
    conds = []
    for cond in conds2:
        conds.append("%s and rev_page in (select cl_from from categorylinks where cl_to='%s')" % (cond, re.sub(' ', '_', category_title).encode('utf-8'))) #fix cuidado con nombres de categorías con '
    headers = ["Edits in category %s (all users)" % category_title, "Edits in category %s (only anonymous users)" % category_title, "Edits in category %s (only registered users)" % category_title]
    generateTimeActivity(time="hour", type="categories", fileprefix="category_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(time="dayofweek", type="categories", fileprefix="category_%d" % page_id, conds=conds, headers=headers, page_id=page_id)
    generateTimeActivity(time="month", type="categories", fileprefix="category_%d" % page_id, conds=conds, headers=headers, page_id=page_id)

def generateUsersTimeActivity(user_id):
    user_name = users[user_id]["user_name"]
    if user_name == user_id: #ip
        conds = ["rev_user_text='%s'" % user_id, "page_namespace=0 and rev_user_text='%s'" % user_id, "page_namespace=1 and rev_user_text='%s'" % user_id] # artículo o todas, #todo añadir escape() para comillas?
    else:
        conds = ["rev_user=%d" % user_id, "page_namespace=0 and rev_user=%d" % user_id, "page_namespace=1 and rev_user=%d" % user_id] # artículo o todas
    headers = ["Edits by %s (all pages)" % user_name, "Edits by %s (only articles)" % user_name, "Edits by %s (only articles talks)" % user_name]
    generateTimeActivity(time="hour", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)
    generateTimeActivity(time="dayofweek", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)
    generateTimeActivity(time="month", type="users", fileprefix="user_%s" % user_id, conds=conds, headers=headers, user_id=user_id)

def generateCloud(type, user_id=None, page_id=None, category_id=None, page_ids=[]):
    cloud = {}

    for rev_id, rev_props in revisions.items():
        if type=="users":
            if user_id:
                if rev_props["rev_user"] != user_id:
                    continue
            else:
                print u"Llamada a función tipo users sin user_id"
                sys.exit()
        elif type=="pages":
            if page_id:
                if rev_props["rev_page"] != page_id:
                    continue
            else:
                print u"Llamada a función tipo pages sin page_id"
                sys.exit()
        elif type=="categories":
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

def printHTML(type, file="", title="", body=""):
    stylesdir = "styles"
    if file:
        file = "%s/html/%s/%s" % (preferences["outputDir"], type, file)
        stylesdir = "../../%s" % stylesdir
    else:
        file = "%s/%s" % (preferences["outputDir"], preferences["indexFilename"])

    f = open(file, "w")
    output = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es" dir="ltr">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link rel="stylesheet" href="%s/style.css" type="text/css" media="all" />
    <title>StatMediaWiki: %s</title>
    </head>
    <body>
    <h1>StatMediaWiki: %s</h1>
    %s
    <hr />
    <center>
    <p>Generated with <a href="http://statmediawiki.forja.rediris.es/">StatMediaWiki</a></p>
    <p><a href="http://validator.w3.org/check?uri=referer"><img src="http://www.w3.org/Icons/valid-xhtml10" alt="Valid XHTML 1.0 Transitional" height="31" width="88" /></a></p>
    </center>
    </body>
    </html>""" % (stylesdir, title, title, body)

    f.write(output.encode("utf-8"))
    f.close()

def printLinesGraph(title, file, labels, headers, rows):
    xticsperiod = ""
    c = 0
    fecha = preferences["startDate"]
    fechaincremento=datetime.timedelta(days=1)
    while fecha <= preferences["endDate"]:
        if fecha.day in [1, 15]:
            xticsperiod += '"%s" %s,' % (fecha.strftime("%Y-%m-%d"), c)
        fecha += fechaincremento
        c += 1
    xticsperiod = xticsperiod[:len(xticsperiod)-1]

    gp = Gnuplot.Gnuplot()
    gp('set data style lines')
    gp('set grid ytics mytics')
    gp("set key left top")
    #gp('set line_width 8')
    gp('set title "%s"' % title.encode("utf-8"))
    gp('set xlabel "%s"' % labels[0].encode("utf-8"))
    gp('set ylabel "%s"' % labels[1].encode("utf-8"))
    gp('set mytics 2')
    gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xticsperiod.encode("utf-8"))
    plots = []
    c = 0
    for row in rows:
        plots.append(Gnuplot.PlotItems.Data(rows[c], with_="lines", title=headers[c+1].encode("utf-8")))
        c += 1
    if len(plots) == 1:
        gp.plot(plots[0])
    elif len(plots) == 2:
        gp.plot(plots[0], plots[1])
    elif len(plots) == 3:
        gp.plot(plots[0], plots[1], plots[2])
    elif len(plots) == 4:
        gp.plot(plots[0], plots[1], plots[2], plots[3])

    gp.hardcopy(filename=file, terminal="png")
    gp.close()

def printBarsGraph(title, file, headers, rows):
    convert = {}
    convert["hour"] = {"0":"00", "1":"01", "2":"02", "3":"03", "4":"04", "5":"05", "6":"06", "7":"07", "8":"08", "9":"09", "10":"10", "11":"11", "12":"12", "13":"13", "14":"14", "15":"15", "16":"16", "17":"17", "18":"18", "19":"19", "20":"20", "21":"21", "22":"22", "23":"23"}
    convert["dayofweek"] = {"0":"Sun", "1":"Mon", "2":"Tue", "3":"Wed", "4":"Thu", "5":"Fri", "6":"Sat"}
    convert["month"] = {"0":"Jan", "1":"Feb", "2":"Mar", "3":"Apr", "4":"May", "5":"Jun", "6":"Jul", "7":"Aug", "8":"Sep", "9":"Oct", "10":"Nov", "11":"Dec"}
    convert2 = {"hour":"Hour", "dayofweek":"Day of week", "month":"Month"}
    xtics = ""
    for xtic in rows[0]:
        xtic_ = convert[headers[0]][str(xtic)]
        xtics += '"%s" %s, ' % (xtic_, xtic)
    xtics = xtics[:-2]
    #print xtics
    gp = Gnuplot.Gnuplot()
    gp("set style data boxes")
    gp("set key left top")
    gp("set grid ytics mytics")
    gp('set title "%s"' % title.encode("utf-8"))
    gp('set xlabel "%s"' % convert2[headers[0]].encode("utf-8"))
    gp('set mytics 2')
    gp('set ylabel "Edits"')
    #gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xtics.encode("utf-8"))
    c = 1
    plots = []
    for row in rows[1:]:
        plots.append(Gnuplot.PlotItems.Data(rows[c], with_="boxes", title=headers[c].encode("utf-8")))
        c += 1
    if len(rows)-1 == 1:
        gp.plot(plots[0])
    elif len(rows)-1 == 2:
        gp.plot(plots[0], plots[1])
    elif len(rows)-1 == 3:
        gp.plot(plots[0], plots[1], plots[2])
    gp.hardcopy(filename=file,terminal="png")
    gp.close()

def printGraphContentEvolution(type, fileprefix, title, headers, rows):
    labels = ["Date (YYYY-MM-DD)", "Bytes"]
    file = "%s/graphs/%s/%s_content_evolution.png" % (preferences["outputDir"], type, fileprefix)
    printLinesGraph(title=title, file=file, labels=labels, headers=headers, rows=rows)

def printGraphTimeActivity(type, fileprefix, title, headers, rows):
    file = "%s/graphs/%s/%s_activity.png" % (preferences["outputDir"], type, fileprefix)
    printBarsGraph(title=title, file=file, headers=headers, rows=rows)

def generateContentEvolution(type, user_id=None, page_id=None, category_id=None, page_ids=[]):
    fecha = preferences["startDate"]
    fechaincremento = datetime.timedelta(days=1)
    graph1 = []
    graph2 = []
    graph3 = []
    count1 = 0
    count2 = 0
    count3 = 0
    while fecha < preferences["endDate"]:
        for rev_id, rev_props in revisions.items():
            if type == "general":
                pass #nos interesan todas
            elif type == "users":
                if not user_id:
                    print "Error: no hay user_id"
                    sys.exit()
                if rev_props["rev_user"] != user_id:
                    continue #nos la saltamos, no es de este usuario
            elif type=="pages":
                if not page_id:
                    print "Error: no hay page_id"
                    sys.exit()
                if rev_props["rev_page"] != page_id:
                    continue #nos la saltamos, no es de esta página
            elif type=="categories":
                if not category_id: #no poner not page_ids, ya que la categoría puede estar vacía y no tener page_id de página alguna
                    print "Error: no hay category_id"
                    sys.exit()
                if rev_props["rev_page"] not in page_ids:
                    continue #nos la saltamos, esta revisión no es de una página de esta categoría

            if rev_props["rev_timestamp"] < fecha and rev_props["rev_timestamp"] >= fecha - fechaincremento: # 00:00:00 < fecha < 23:59:59
                rev_page = rev_props["rev_page"]
                if type == "general":
                    #más adelante quizás convenga poner la evolución del contenido según anónimos y registrados, para el caso general
                    if pages[rev_page]["page_namespace"] == 0:
                        count2 += rev_props["len_diff"]
                    if pages[rev_page]["page_namespace"] == 1:
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
                    if pages[rev_page]["page_namespace"] == 0:
                        count2 += rev_props["len_diff"]
                    if pages[rev_page]["page_namespace"] == 1:
                        count3 += rev_props["len_diff"]
                    #evolución de todas las páginas
                    count1 += rev_props["len_diff"]

        graph1.append(count1)
        graph2.append(count2)
        graph3.append(count3)

        fecha += fechaincremento

    if type == "users":
        users[user_id]["bytesbynamespace"]["*"] = count1
        users[user_id]["bytesbynamespace"][0] = count2

    title = u""
    fileprefix = u""
    owner = u""
    if type == "general":
        title = u"Content evolution in %s" % preferences["siteName"]
        fileprefix = "general"
        owner = preferences["siteName"]
    elif type == "users":
        user_name = users[user_id]["user_name"]
        title = u"Content evolution by %s" % user_name
        fileprefix = "user_%s" % user_id
        owner = user_name
    elif type == "pages":
        page_title = pages[page_id]["page_title"]
        title = u"Content evolution in %s" % page_title
        fileprefix = "page_%s" % page_id
        owner = page_title
    elif type == "categories":
        category_title = pages[category_id]["page_title"]
        title = u"Content evolution for pages in %s" % category_title
        fileprefix = "category_%s" % category_id
        owner = category_title

    #falta csv
    if type == "pages" or type == "categories":
        headers = ["Date", "%s content (all users)" % owner, "%s content (only anonymous users)" % owner, "%s content (only registered users)" % owner]
    else:
        headers = ["Date", "%s content (all pages)" % owner, "%s content (only articles)" % owner, "%s content (only articles talks)" % owner]

    if type == "users" and preferences["anonymous"]:
        pass #no print graph
    else:
        printCSV(type=type, subtype="content_evolution", fileprefix=fileprefix,
                 headers=headers,
                 rows=[generadorColumnaFechas(preferences["startDate"]),
                       graph1, graph2, graph3])
        printGraphContentEvolution(type=type, fileprefix=fileprefix,
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
    for user_id, user_props in users.items():
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
        user_props = users[user_id]
        edits_percent = user_props["revisionsbynamespace"]["*"] / (edits / 100.0)
        editsinarticles_percent = user_props["revisionsbynamespace"][0] / (editsinarticles / 100.0)
        bytes_percent = user_props["bytesbynamespace"]["*"] / (bytes / 100.0)
        bytesinarticles_percent = user_props["bytesbynamespace"][0] / (bytesinarticles / 100.0)
        if preferences["anonymous"]:
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
    for page_id, page_props in pages.items():
        edits += page_props["edits"]
        bytes += page_props["page_len"]
        visits += page_props["page_counter"]
        sortedPages.append([page_props["edits"], page_id])
    sortedPages.sort()
    sortedPages.reverse()

    c = 1
    for page_edits, page_id in sortedPages:
        page_props = pages[page_id]
        edits_percent = page_props["edits"] / (edits / 100.0)
        bytes_percent = page_props["page_len"] / (bytes / 100.0)
        visits_percent = page_props["page_counter"] / (visits / 100.0)
        output += u"""<tr><td>%s</td><td><a href="html/pages/page_%s.html">%s</a></td><td>%s</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td></tr>\n""" % (c, page_id, page_props["page_title"], namespaces[page_props["page_namespace"]], page_props["edits"], edits_percent, page_props["page_len"], bytes_percent, page_props["page_counter"], visits_percent)
        c += 1

    output += """<tr><td></td><td>Total</td><td></td><td>%s (100%%)</td><td>%s (100%%)</td><td>%s (100%%)</td></tr>\n""" % (edits, bytes, visits)
    output += """</table>"""

    return output

def generateUsersMostEditedTable(user_id):
    output = u"""<table>
    <tr><th>#</th><th>Page</th><th>Namespace</th><th>Edits</th></tr>"""

    most_edited = {}
    for rev_id in users[user_id]["revisions"]:
        rev_page = revisions[rev_id]["rev_page"]
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
        page_title = pages[rev_page]["page_title"]
        page_namespace = pages[rev_page]["page_namespace"]
        output += u"""<tr><td>%s</td><td><a href="../pages/page_%s.html">%s</a></td><td>%s</td><td><a href="%s/index.php?title=%s&amp;action=history">%s</a></td></tr>\n""" % (c, rev_page, page_title, namespaces[page_namespace], preferences["siteUrl"], page_title, edits)
    output += u"""<tr><td></td><td>Total</td><td></td><td>%s</td></tr>""" % (users[user_id]["revisionsbynamespace"]["*"])

    output += u"""</table>"""

    return output

def generatePagesTopUsersTable(page_id):
    if preferences["anonymous"]:
        return u"""<p>This is an anonymous analysis. This information will not be showed.</p>\n"""

    output = u"""<table>
    <tr><th>#</th><th>User</th><th>Edits</th></tr>"""

    top_users = {}
    for rev_id in pages[page_id]["revisions"]:
        rev_user = revisions[rev_id]["rev_user"]
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
        user_name = users[rev_user]["user_name"]
        page_title = pages[page_id]["page_title"]
        output += u"""<tr><td>%s</td><td><a href="../users/user_%s.html">%s</a></td><td><a href="%s/index.php?title=%s&amp;action=history">%s</a></td></tr>\n""" % (c, rev_user, user_name, preferences["siteUrl"], page_title, edits)
    output += u"""<tr><td></td><td>Total</td><td>%s</td></tr>""" % (len(pages[page_id]["revisions"]))

    output += u"""</table>"""

    return output

def generateGeneralAnalysis():
    print "Generating general analysis"
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

    cursor.execute("SELECT SUM(page_counter) AS count FROM %spage WHERE 1" % preferences["tablePrefix"])
    dict["totalvisits"] = cursor.fetchall()[0][0]

    cursor.execute("SELECT COUNT(*) AS count FROM %simage WHERE 1" % preferences["tablePrefix"])
    dict["totalfiles"] = cursor.fetchall()[0][0]
    dateGenerated = datetime.datetime.now().isoformat()
    period = "%s &ndash; %s" % (preferences["startDate"].isoformat(), preferences["endDate"].isoformat())

    body = u"""<table class="sections">
    <tr><th><b>Sections</b></th></tr>
    <tr><td><a href="#contentevolution">Content evolution</a></td></tr>
    <tr><td><a href="#activity">Activity</a></td></tr>
    <tr><td><a href="#users">Users</a></td></tr>
    <tr><td><a href="#pages">Pages</a></td></tr>
    <tr><td><a href="#tagscloud">Tags cloud</a></td></tr>
    </table>
    <dl>
    <dt>Site:</dt>
    <dd><a href='%s'>%s</a></dd>
    <dt>Report period:</dt>
    <dd>%s &ndash; %s</dd>
    <dt>Total pages:</dt>
    <dd><a href="#pages">%s</a> (Articles: %s)</dd>
    <dt>Total edits:</dt>
    <dd>%s (In articles: %s)</dd>
    <dt>Total bytes:</dt>
    <dd>%s (In articles: %s)</dd>
    <dt>Total visits:</dt>
    <dd>%s</dd>
    <dt>Total files:</dt>
    <dd><a href="%s/%s/Special:Imagelist">%s</a></dd>
    <dt>Users:</dt>
    <dd><a href="#users">%s</a></dd>
    <dt>Generated:</dt>
    <dd>%s</dd>
    </dl>
    <h2 id="contentevolution">Content evolution</h2>
    <center>
    <img src="graphs/general/general_content_evolution.png" alt="Content evolution" />
    </center>
    <h2 id="activity">Activity</h2>
    <center>
    <img src="graphs/general/general_hour_activity.png" alt="Hour activity" />
    <img src="graphs/general/general_dayofweek_activity.png" alt="Day of week activity" />
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
    <h2 id="tagscloud">Tags cloud</h2>
    <center>
    %s
    </center>
    """ % (preferences["siteUrl"], preferences["siteName"], preferences["startDate"].isoformat(), preferences["endDate"].isoformat(), dict["totalpages"], dict["totalarticles"], dict["totaledits"], dict["totaleditsinarticles"], dict["totalbytes"], dict["totalbytesinarticles"], dict["totalvisits"], preferences["siteUrl"], preferences["subDir"], dict["totalfiles"], dict["totalusers"], datetime.datetime.now().isoformat(), generateUsersTable(), generatePagesTable(), generateGeneralCloud())

    generateGeneralContentEvolution()
    generateGeneralTimeActivity()

    printHTML(type="general", title=preferences["siteName"], body=body)

    destroyConnCursor(conn, cursor)

def generatePagesAnalysis():
    for page_id, page_props in pages.items():
        page_title = page_props["page_title"]
        print u"Generating analysis to the page: %s" % page_title
        generatePagesContentEvolution(page_id=page_id)
        generatePagesTimeActivity(page_id=page_id)

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
        <dd>%s (By anonymous users: %s. By registered users: %s)</dd>
        <dt>Bytes:</dt>
        <dd>%s</dd>
        </dl>
        <h2 id="contentevolution">Content evolution</h2>
        <center>
        <img src="../../graphs/pages/page_%s_content_evolution.png" alt="Content evolution" />
        </center>
        <h2 id="activity">Activity</h2>
        <center>
        <img src="../../graphs/pages/page_%s_hour_activity.png" alt="Hour activity" />
        <img src="../../graphs/pages/page_%s_dayofweek_activity.png" alt="Day of week activity" />
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
        """ % (preferences["indexFilename"], preferences["siteUrl"], preferences["subDir"], page_title, page_title, preferences["siteUrl"], page_title, page_props["edits"], page_props["revisionsbyuserclass"]["anon"], page_props["revisionsbyuserclass"]["reg"], page_props["page_len"], page_id, page_id, page_id, page_id, generatePagesTopUsersTable(page_id=page_id), generatePagesCloud(page_id=page_id))

        title = "%s: %s" % (preferences["siteName"], page_title)
        printHTML(type="pages", file="page_%s.html" % page_id, title=title, body=body)

def generateCategoriesAnalysis():
    for page_id, page_props in pages.items():
        if page_props["page_namespace"] != 14: #only categories (namespace == 14)
            continue

        category_title = ':'.join(page_props["page_title"].split(':')[1:]) #eliminamos el prefijo Category:
        page_ids = []
        if categories.has_key(category_title):
            page_ids = categories[category_title]
        else:
            sys.exit() #no debería entrar aquí
        print u"Generating analysis to the category: %s" % category_title
        generateCategoriesContentEvolution(category_id=page_id, page_ids=page_ids)
        generateCategoriesTimeActivity(page_id=page_id)

        catedits = 0
        for page_id, page_props in pages.items():
            if page_id in page_ids:
                catedits += page_props["edits"]

        catanonedits = 0
        for page_id, page_props in pages.items():
            if page_id in page_ids:
                catanonedits += page_props["revisionsbyuserclass"]["anon"]

        catregedits = 0
        for page_id, page_props in pages.items():
            if page_id in page_ids:
                catregedits += page_props["revisionsbyuserclass"]["reg"]

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
        <dd><a href='%s/%s/%s'>%s</a> (<a href="%s/index.php?title=%s&amp;action=history">history</a>)</dd>
        <dt>Edits to pages in this category:</dt>
        <dd>%s (By anonymous users: %s. By registered users: %s)</dd>
        <dt>Pages:</dt>
        <dd>%s</dd>
        </dl>
        <h2 id="contentevolution">Content evolution</h2>
        <center>
        <img src="../../graphs/categories/page_%s_content_evolution.png" alt="Content evolution" />
        </center>
        <h2 id="activity">Activity</h2>
        <center>
        <img src="../../graphs/categories/category_%s_hour_activity.png" alt="Hour activity" />
        <img src="../../graphs/categories/category_%s_dayofweek_activity.png" alt="Day of week activity" />
        <img src="../../graphs/categories/category_%s_month_activity.png" alt="Month activity" />
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
        """ % (preferences["indexFilename"], preferences["siteUrl"], preferences["subDir"], page_props["page_title"], page_props["page_title"], preferences["siteUrl"], page_props["page_title"], catedits, catanonedits, catregedits, len(categories[category_title]), page_id, page_id, page_id, page_id, "", "", generateCategoriesCloud(category_id=page_id, page_ids=page_ids)) #crear topuserstable para las categorias y fusionarla con generatePagesTopUsersTable(page_id=page_id) del las páginas y el global (así ya todas muestran los incrementos en bytes y porcentajes, además de la ediciones), lo mismo para el top de páginas más editadas

        title = "%s: Pages in category %s" % (preferences["siteName"], category_title)
        printHTML(type="categories", file="category_%s.html" % page_id, title=title, body=body)

def generateUsersAnalysis():
    for user_id, user_props in users.items():
        user_name = user_props["user_name"]
        print u"Generating analysis to user: %s" % user_name
        generateUsersContentEvolution(user_id=user_id) #debe ir antes de rellenar el body, cuenta bytes, y antes de cortar por anonymous
        if preferences["anonymous"]:
            continue
        generateUsersTimeActivity(user_id=user_id)

        gallery = u""
        for img_name in users[user_id]["images"]:
            gallery += u"""<a href='%s/%s/Image:%s'><img src="%s" width="200px" alt="%s"/></a>&nbsp;&nbsp;&nbsp;""" % (preferences["siteUrl"], preferences["subDir"], img_name, images[img_name]["img_url"], img_name)

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
        <dd>%s (In articles: %s)</dd>
        <dt>Bytes added:</dt>
        <dd>%s (In articles: %s)</dd>
        <dt>Files uploaded:</dt>
        <dd><a href="#uploads">%s</a></dd>
        </dl>
        <h2 id="contentevolution">Content evolution</h2>
        <center>
        <img src="../../graphs/users/user_%s_content_evolution.png" alt="Content evolution" />
        </center>
        <h2 id="activity">Activity</h2>
        <center>
        <img src="../../graphs/users/user_%s_hour_activity.png" alt="Hour activity" />
        <img src="../../graphs/users/user_%s_dayofweek_activity.png" alt="Day of week activity" />
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
        """ % (preferences["indexFilename"], preferences["siteUrl"], preferences["subDir"], user_name, user_name, preferences["siteUrl"], preferences["subDir"], user_name, user_props["revisionsbynamespace"]["*"], user_props["revisionsbynamespace"][0], user_props["bytesbynamespace"]["*"], user_props["bytesbynamespace"][0], len(user_props["images"]), user_id, user_id, user_id, user_id, generateUsersMostEditedTable(user_id=user_id), len(users[user_id]["images"]), gallery, generateUsersCloud(user_id=user_id))

        title = "%s: User:%s" % (preferences["siteName"], user_name)
        if not preferences["anonymous"]:
            printHTML(type="users", file="user_%s.html" % user_id, title=title, body=body)

def generateAnalysis():
    #generatePagesAnalysis()
    generateCategoriesAnalysis()
    #generateUsersAnalysis()
    #generateGeneralAnalysis() #necesita el useranalysis antes, para llenar los bytes

def bye():
    print "StatMediaWiki has finished correctly. Closing Gnuplot. Killing process to exit program."
    os.system("kill -9 %s" % os.getpid())

def main():
    welcome()

    getParameters()
    initialize() #dbname required

    loadImages()
    loadRevisions() #require startDate and endDate initialized
    loadPages() #revisions loaded required
    loadUsers() #revisions and uploads loaded required
    loadCategories()

    if preferences["anonymous"]:
        anonimize()

    manageOutputDir()
    generateAnalysis()
    copyFiles()

    bye()

if __name__ == "__main__":
    main()
