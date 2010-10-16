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
if not preferences["currentPath"]:
    preferences["currentPath"] = '.' #current
preferences["anonymous"] = False

