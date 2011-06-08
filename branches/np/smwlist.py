#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2011 StatMediaWiki
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
