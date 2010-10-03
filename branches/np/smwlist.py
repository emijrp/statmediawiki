# -*- coding: utf-8  -*-

import sqlite3

def listofusers(cursor):
    #fix cambiar por una consulta a la tabla user, que tengo que hacer todavía, y meter parametro paradistinguir entre registrados, ips
    a = cursor.execute("select distinct username from revision where 1")
    users = []
    for row in a:
        users.append(row[0])
    users.sort()
    return users

def listofpages(cursor):
    #fix cambiar por la tabla page, meter parametro para filtrar nm?
    a = cursor.execute("select distinct title from revision where 1")
    pages = []
    for row in a:
        pages.append(row[0])
    pages.sort()
    return pages

def listofpagesandedits(cursor):
    #fix cambiar por la tabla page, meter parametro para filtrar nm?
    #fix si la tabla page incluye un campo edits (con el numero de ediciones a esa página), esta consulta puede cargar mucho más rápido, aunque
    #tendríamos un campo "redundante" con información derivada
    a = cursor.execute("select title, count(*) as count from revision where 1 group by title")
    pages = []
    for row in a:
        pages.append([row[0], row[1]])
    pages.sort()
    return pages
