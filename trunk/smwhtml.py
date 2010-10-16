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

def printHTML(type=None, file="", title="", body=""):
    stylesdir = "styles"
    if file:
        file = "%s/html/%s/%s" % (smwconfig.preferences["outputDir"], type, file)
        stylesdir = "../../%s" % stylesdir
    else:
        file = "%s/%s" % (smwconfig.preferences["outputDir"], smwconfig.preferences["indexFilename"])

    f = open(file, "w")
    output = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es" dir="ltr">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link rel="stylesheet" href="%s/style.css" type="text/css" media="all" />
    <title>StatMediaWiki: %s</title>
    </head>
    <body>
    <h1>StatMediaWiki: %s</h1>
    %s
    <hr />
    <center>
    <p>Generated with <a href="http://statmediawiki.forja.rediris.es/">StatMediaWiki</a></p>
    <p><a href="http://validator.w3.org/check?uri=referer"><img src="http://www.w3.org/Icons/valid-xhtml10" alt="Valid XHTML 1.0 Transitional" height="31" width="88" /></a></p>
    </center>
    </body>
    </html>""" % (stylesdir, title, title, body)

    f.write(output.encode("utf-8"))
    f.close()
