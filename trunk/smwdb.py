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

import MySQLdb
import sys

import smwconfig

def createConnCursor():
    conn = MySQLdb.connect(db=smwconfig.preferences["dbName"], read_default_file='~/.my.cnf', use_unicode=False) #pedir ruta absoluta del fichero cnf? #todo
    cursor = conn.cursor()
    try:
        conn = MySQLdb.connect(db=smwconfig.preferences["dbName"], read_default_file='~/.my.cnf', use_unicode=False) #pedir ruta absoluta del fichero cnf? #todo
        cursor = conn.cursor()
    except:
        print "Hubo un error al conectarse a la base de datos"
        sys.exit()
    return conn, cursor

def destroyConnCursor(conn, cursor):
    cursor.close()
    conn.close()

