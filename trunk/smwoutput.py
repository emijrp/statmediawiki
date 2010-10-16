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
import sys

import smwconfig

def manageOutputDir():
    #Generando estructura de directorios
    directories = [
        smwconfig.preferences["outputDir"],
        "%s/csv" % smwconfig.preferences["outputDir"],
        "%s/csv/general" % smwconfig.preferences["outputDir"],
        "%s/csv/users" % smwconfig.preferences["outputDir"],
        "%s/csv/pages" % smwconfig.preferences["outputDir"],
        "%s/csv/categories" % smwconfig.preferences["outputDir"],
        "%s/graphs" % smwconfig.preferences["outputDir"],
        "%s/graphs/general" % smwconfig.preferences["outputDir"],
        "%s/graphs/users" % smwconfig.preferences["outputDir"],
        "%s/graphs/pages" % smwconfig.preferences["outputDir"],
        "%s/graphs/categories" % smwconfig.preferences["outputDir"],
        "%s/html" % smwconfig.preferences["outputDir"],
        "%s/html/general" % smwconfig.preferences["outputDir"],
        "%s/html/users" % smwconfig.preferences["outputDir"],
        "%s/html/pages" % smwconfig.preferences["outputDir"],
        "%s/html/categories" % smwconfig.preferences["outputDir"],
        "%s/js" % smwconfig.preferences["outputDir"],
        "%s/styles" % smwconfig.preferences["outputDir"],
    ]
    for directory in directories:
        if not os.path.exists(directory) or not os.path.isdir(directory):
            try:
                os.makedirs(directory)
                print "Creando %s" % directory
            except:
                print "Hubo un error al intentar crear la ruta %s" % directory
                sys.exit()

def copyFiles():
    #Copiando ficheros individuales
    #Van en el nivel principal (están duplicados con la línea anterior)
    os.system("cp %s/styles/*.css %s/styles" % (smwconfig.preferences["currentPath"], smwconfig.preferences["outputDir"]))
    os.system("cp %s/js/*.js %s/js" % (smwconfig.preferences["currentPath"], smwconfig.preferences["outputDir"]))
    #Los CSV no se copian, se generan directamente en outputdir
    #os.system("cp %s/csv/general/*.csv %s/csv/general" % (smwconfig.preferences["currentPath"], smwconfig.preferences["outputDir"]))
    #os.system("cp %s/csv/pages/*.csv %s/csv/pages" % (smwconfig.preferences["currentPath"], smwconfig.preferences["outputDir"]))
    #os.system("cp %s/csv/users/*.csv %s/csv/users" % (smwconfig.preferences["currentPath"], smwconfig.preferences["outputDir"]))
