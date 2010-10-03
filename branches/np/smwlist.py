# -*- coding: utf-8  -*-

import sqlite3

def listofusers(cursor):
    a = cursor.execute("select username from user where 1")
    users = []
    for row in a:
        users.append(row[0])
    users.sort()
    return users

def listofusersandedits(cursor):
    a = cursor.execute("select username, editcount from user where 1")
    users = []
    for row in a:
        users.append([row[0], row[1]])
    users.sort()
    return users

def listofpages(cursor):
    a = cursor.execute("select title from page where 1")
    pages = []
    for row in a:
        pages.append(row[0])
    pages.sort()
    return pages

def listofpagesandedits(cursor):
    a = cursor.execute("select title, editcount from page where 1")
    pages = []
    for row in a:
        pages.append([row[0], row[1]])
    pages.sort()
    return pages
