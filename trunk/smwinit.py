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

import datetime
import getopt
import os
import sys

import smwconfig
import smwdb

def welcome():
    print "-"*75
    print u"""Welcome to StatMediaWiki %s. Web: http://statmediawiki.forja.rediris.es""" % (smwconfig.CURRENT_VERSION)
    print "-"*75

def bye():
    print "StatMediaWiki has finished correctly. Closing Gnuplot. Killing process to exit program."
    os.system("kill -9 %s" % os.getpid())

def usage():
    filename = "help.txt"
    if smwconfig.preferences["currentPath"]:
        filename = "%s/%s" % (smwconfig.preferences["currentPath"], filename)
    f = open(filename, "r")
    print f.read()
    f.close()
    sys.exit() #mostramos ayuda y salimos

def getParameters():
    #console params
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["h", "help", "anonymous", "outputdir=", "index=", "sitename=", "subdir=", "siteurl=", "dbname=", "tableprefix=", "startdate=", "enddate="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("--outputdir"):
            smwconfig.preferences["outputDir"] = a
            while len(smwconfig.preferences["outputDir"])>0:
                if smwconfig.preferences["outputDir"][-1] == '/': #dará problemas con rutas windows?
                    smwconfig.preferences["outputDir"] = smwconfig.preferences["outputDir"][:-1]
                else:
                    break
            if not smwconfig.preferences["outputDir"]:
                smwconfig.preferences["outputDir"] = '.'
        elif o in ("--index"):
            smwconfig.preferences["indexFilename"] = a
        elif o in ("--sitename"):
            smwconfig.preferences["siteName"] = a
        elif o in ("--siteurl"):
            smwconfig.preferences["siteUrl"] = a
        elif o in ("--subdir"):
            smwconfig.preferences["subDir"] = a
        elif o in ("--dbname"):
            smwconfig.preferences["dbName"] = a
        elif o in ("--tableprefix"):
            smwconfig.preferences["tablePrefix"] = a
        elif o in ("--startdate"):
            smwconfig.preferences["startDate"] = datetime.datetime(year=int(a.split("-")[0]), month=int(a.split("-")[1]), day=int(a.split("-")[2]), hour=0, minute=0, second=0)
        elif o in ("--enddate"):
            smwconfig.preferences["endDate"] = datetime.datetime(year=int(a.split("-")[0]), month=int(a.split("-")[1]), day=int(a.split("-")[2]), hour=0, minute=0, second=0)
        elif o in ("--anonymous"):
            smwconfig.preferences["anonymous"] = True
        else:
            assert False, "unhandled option"

    #gestionar falta de parametros
    if not smwconfig.preferences["dbName"] or \
       not smwconfig.preferences["siteUrl"] or \
       not smwconfig.preferences["siteName"]:
        print u"""Error. Parameters --dbname, --siteurl and --sitename are required. Write --help for help."""
        sys.exit()
        #usage()

    #fin gestionar falta parametros
