#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2012 StatMediaWiki
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
    result = cursor.execute("SELECT user_name FROM user WHERE 1")
    users = [row[0] for row in result]
    users.sort()
    return users

def listofusersandedits(cursor, orderby='user_name', order='ASC', limit=-1, offset=0):
    result = cursor.execute("SELECT user_name, user_editcount FROM user WHERE 1 ORDER BY %s %s LIMIT %s OFFSET %s" % (orderby, order, limit, offset))
    users = [[user_name, user_editcount] for user_name, user_editcount in result]
    return users

def listofpages(cursor):
    result = cursor.execute("SELECT page_title FROM page WHERE 1")
    pages = [row[0] for row in result]
    pages.sort()
    return pages

def listofpagesandedits(cursor, orderby='page_title', order='ASC', limit=-1, offset=0):
    result = cursor.execute("SELECT page_title, page_editcount FROM page WHERE 1 ORDER BY %s %s LIMIT %s OFFSET %s" % (orderby, order, limit, offset))
    pages = [[page_title, page_editcount] for page_title, page_editcount in result]
    return pages
