# -*- coding: utf-8  -*-

import sqlite3

def listofusers(cursor):
    result = cursor.execute("select user_name from user where 1")
    users = []
    for row in result:
        users.append(row[0])
    users.sort()
    return users

def listofusersandedits(cursor):
    result = cursor.execute("select user_name, user_editcount from user where 1")
    users = []
    for user_name, user_editcount in result:
        users.append([user_name, user_editcount])
    users.sort()
    return users

def listofpages(cursor):
    result = cursor.execute("select page_title from page where 1")
    pages = []
    for row in result:
        pages.append(row[0])
    pages.sort()
    return pages

def listofpagesandedits(cursor):
    result = cursor.execute("select page_title, page_editcount from page where 1")
    pages = []
    for page_title, page_editcount in result:
        pages.append([page_title, page_editcount])
    pages.sort()
    return pages
