#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010, 2011 StatMediaWiki
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

import re
import os
import datetime

#version info
CURRENT_VERSION = '1.1'

#data
categories = {}
images = {}
namespaces = {}
pages = {}
preferences = {}
revisions = {}
users = {}

#user preferences
preferences["codification"] = 'iso-8859-1' # 'iso-8859-1' makes history bytes equal in MediaWiki and StatMediaWiki (when accent appears)
preferences['codification_'] = re.sub('-', '_', preferences["codification"]) # for Gnuplot
preferences["outputDir"] = 'output'
preferences["indexFilename"] = 'index.html'
preferences["siteName"] = 'wikitest'
preferences["siteUrl"] = 'http://localhost/mediawiki'
preferences["subDir"] = 'index.php' #MediaWiki subdir, usually "index.php" in http://osl.uca.es/wikihaskell/index.php/Main_Page
preferences["dbName"] = 'my_wiki_test'
preferences["tablePrefix"] = '' #Usually empty
#dates, we use datetime python objects, the rows in MediaWiki dbs uses this format yyyymmddhhmmss http://www.mediawiki.org/wiki/Manual:Timestamp
preferences["startDate"] = '' #auto, start point for date range
preferences["endDate"] = datetime.datetime(2010, 2, 15, 00, 01) #auto, end point for date range
preferences["startDateMW"] = ''
preferences["endDateMW"] = ''
#WARNING: the focused dates can produce a big amunt of charge on the system, the longer distance between dates, the bigger charge on the system
preferences["startDateFocused"] = datetime.datetime(2009, 10, 1, 8, 45) #CANNOT be auto, start point for "Focused" graphs
preferences["endDateFocused"] = datetime.datetime(2009, 10, 1, 10, 01) #CANNOT be auto, end point for "Focused" graphs
#enddates

preferences["currentPath"] = os.path.dirname(__file__)
if not preferences["currentPath"]:
    preferences["currentPath"] = '.' #current
preferences["anonymous"] = False
preferences["numColors"] = 10 #depends on style.css
