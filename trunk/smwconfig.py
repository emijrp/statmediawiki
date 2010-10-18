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

import os

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
preferences["outputDir"] = 'output'
preferences["indexFilename"] = 'index.html'
preferences["siteName"] = ''
preferences["siteUrl"] = ''
preferences["subDir"] = 'index.php' #MediaWiki subdir, usually "index.php" in http://osl.uca.es/wikihaskell/index.php/Main_Page
preferences["dbName"] = ''
preferences["tablePrefix"] = '' #Usually empty
#dates, we use datetime python objects, the rows in MediaWiki dbs uses this format yyyymmddhhmmss http://www.mediawiki.org/wiki/Manual:Timestamp
preferences["startDate"] = '' #auto, start point for date range
preferences["endDate"] = '' #auto, end point for date range
preferences["startDateMW"] = ''
preferences["endDateMW"] = ''
#enddates

preferences["currentPath"] = os.path.dirname(__file__)
if not preferences["currentPath"]:
    preferences["currentPath"] = '.' #current
preferences["anonymous"] = False
preferences["numColors"] = 10 #depends on style.css
