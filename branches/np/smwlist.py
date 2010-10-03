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
