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

import smwconfig

def getBacklink():
    return '&lt;&lt; <a href="../../%s">Back</a>' % (smwconfig.preferences["indexFilename"])

def getSections(type=None):
    output = '<table class="sections">'
    output += '<tr><th><b>Sections</b></th></tr>'
    output += '<tr><td><a href="#contentevolution">Content evolution</a></td></tr>'
    output += '<tr><td><a href="#activity">Activity</a></td></tr>'
    if type != "users":
        output += '<tr><td><a href="#topusers">Top users</a></td></tr>'
    if type != "pages":
        output += '<tr><td><a href="#toppages">Top pages</a></td></tr>'
    if type == "global":
        output += '<tr><td><a href="#topcategories">Top categories</a></td></tr>'
    if type == "users":
        output += '<tr><td><a href="#uploads">Uploads</a></td></tr>'
    output += '<tr><td><a href="#tagscloud">Tags cloud</a></td></tr>'
    output += '</table>'

    return output

def getLegend():
    output = '<table><tr><td>&nbsp;&nbsp;Low&nbsp;&nbsp;</td>'
    output += ''.join(['<td class="cellcolor%d">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>' % (i) for i in range(smwconfig.preferences["numColors"])])
    output += '<td>&nbsp;&nbsp;High&nbsp;&nbsp;</td></tr></table>'
    return output

def printHTML(type=None, file="", title="", body=""):
    stylesdir = "styles"
    jsdir = "js"
    if file:
        file = "%s/html/%s/%s" % (smwconfig.preferences["outputDir"], type, file)
        stylesdir = "../../%s" % stylesdir
        jsdir = "../../%s" % jsdir
    else:
        file = "%s/%s" % (smwconfig.preferences["outputDir"], smwconfig.preferences["indexFilename"])

    f = open(file, "w")
    output = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es" dir="ltr">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link rel="stylesheet" href="%s/style.css" type="text/css" media="all" />
    <script src="%s/common.js" type="text/javascript"></script>
    <title>StatMediaWiki: %s</title>
    </head>
    <body>
    <h1>StatMediaWiki: %s</h1>
    %s

    <h2 id="about">About</h2>
    <!-- icons -->
    <span style="float: right;"><a href="http://validator.w3.org/check?uri=referer"><img src="http://www.w3.org/Icons/valid-xhtml10" alt="Valid XHTML 1.0 Transitional" height="31" width="88" /></a></span>
    <p>Generated with <a href="http://statmediawiki.forja.rediris.es/">StatMediaWiki</a>.
    </p>
    </body>
    </html>""" % (stylesdir, jsdir, title, title, body)

    f.write(output.encode("utf-8"))
    f.close()
