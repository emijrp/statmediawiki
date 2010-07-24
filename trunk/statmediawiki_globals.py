#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010
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

# User preferences
global preferences
preferences = {}

preferences["outputDir"] = "output"
preferences["indexFilename"] = "index.html"
preferences["siteName"] = "YourWikiSite"
preferences["siteUrl"] = "http://youwikisite.org"
preferences["subDir"] = "/index.php" #MediaWiki subdir, usually index.php/
preferences["dbName"] = "yourwikidb"
preferences["tablePrefix"] = "" #Usually empty
preferences["startDate"] = "" #If wanted, start point for date range
preferences["endDate"] = "" #If wanted, end point for date range
preferences["currentPath"] = os.path.dirname(__file__)
