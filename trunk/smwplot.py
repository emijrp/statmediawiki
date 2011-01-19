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

import datetime
import Gnuplot
import re

import smwconfig

def printFilledcurvesGraph(title, file, labels, headers, rows):
    xticsperiod = ""
    c = 0
    fecha = smwconfig.preferences["startDate"]
    fechaincremento=datetime.timedelta(days=1)
    while fecha <= smwconfig.preferences["endDate"]:
        if fecha.day in [1, 15]:
            xticsperiod += '"%s" %s,' % (fecha.strftime("%Y-%m-%d"), c)
        fecha += fechaincremento
        c += 1
    xticsperiod = xticsperiod[:len(xticsperiod)-1]

    gp = Gnuplot.Gnuplot()
    gp('set encoding %s' % smwconfig.preferences['codification_'])
    gp('set yrange [0:100]')
    gp('set key under nobox')
    gp('set title "%s"' % title.encode(smwconfig.preferences['codification']))
    gp('set xlabel "%s"' % labels[0].encode(smwconfig.preferences['codification']))
    gp('set ylabel "%s"' % labels[1].encode(smwconfig.preferences['codification']))
    gp('set xtics rotate by 90')
    gp('set xtics (%s)' % (xticsperiod.encode(smwconfig.preferences['codification'])))
    plots = []
    c = 0
    for row in rows:
        plots.append(Gnuplot.PlotItems.Data(row, with_="filledcurve", title=headers[c].encode(smwconfig.preferences['codification']))) #steps, filledcurve, ?
        c += 1
    gp.plot(*plots)
    gp.hardcopy(filename=file, terminal="png")
    gp.close()

def printLinesGraph(title, file, labels, headers, rows):
    xticsperiod = ""
    c = 0
    fecha = smwconfig.preferences["startDate"]
    fechaincremento=datetime.timedelta(days=1)
    while fecha <= smwconfig.preferences["endDate"]:
        if fecha.day in [1, 15]:
            xticsperiod += '"%s" %s,' % (fecha.strftime("%Y-%m-%d"), c)
        fecha += fechaincremento
        c += 1
    xticsperiod = xticsperiod[:len(xticsperiod)-1]

    gp = Gnuplot.Gnuplot()
    #gp('set term png')
    gp('set encoding %s' % smwconfig.preferences['codification_'])
    gp('set data style lines')
    gp('set grid ytics mytics')
    gp("set key left top")
    #gp('set line_width 8')
    gp('set title "%s"' % title.encode(smwconfig.preferences['codification']))
    gp('set xlabel "%s"' % labels[0].encode(smwconfig.preferences['codification']))
    gp('set ylabel "%s"' % labels[1].encode(smwconfig.preferences['codification']))
    gp('set mytics 2')
    gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xticsperiod.encode(smwconfig.preferences['codification']))
    plots = []
    c = 0
    for row in rows:
        plots.append(Gnuplot.PlotItems.Data(row, with_="lines", title=headers[c+1].encode(smwconfig.preferences['codification'])))
        c += 1
    gp.plot(*plots)
    gp.hardcopy(filename=file, terminal="png")
    gp.close()

def printBarsGraph(title, filename, headers, rows):
    convert = {}
    convert["hour"] = {"0":"00", "1":"01", "2":"02", "3":"03", "4":"04", "5":"05", "6":"06", "7":"07", "8":"08", "9":"09", "10":"10", "11":"11", "12":"12", "13":"13", "14":"14", "15":"15", "16":"16", "17":"17", "18":"18", "19":"19", "20":"20", "21":"21", "22":"22", "23":"23"}
    convert["dayofweek"] = {"0":"Sun", "1":"Mon", "2":"Tue", "3":"Wed", "4":"Thu", "5":"Fri", "6":"Sat"}
    convert["weekofyear"] = {}
    for i in range(53):
        convert["weekofyear"][str(i)] = str(i+1)
    convert["month"] = {"0":"Jan", "1":"Feb", "2":"Mar", "3":"Apr", "4":"May", "5":"Jun", "6":"Jul", "7":"Aug", "8":"Sep", "9":"Oct", "10":"Nov", "11":"Dec"}
    convert2 = {"hour":"Hour", "dayofweek":"Day of week", "weekofyear": "Week", "month":"Month"}
    xtics = ""
    for xtic in rows[0]:
        xtic_ = convert[headers[0]][str(xtic)]
        xtics += '"%s" %s, ' % (xtic_, xtic)
    xtics = xtics[:-2]
    #print xtics
    gp = Gnuplot.Gnuplot()
    #gp('set term png')
    gp('set encoding %s' % smwconfig.preferences['codification_'])
    gp("set style data boxes")
    gp("set key left top")
    gp("set grid ytics mytics")
    gp('set title "%s"' % title.encode(smwconfig.preferences['codification']))
    gp('set xlabel "%s"' % convert2[headers[0]].encode(smwconfig.preferences['codification']))
    gp('set mytics 2')
    gp('set ylabel "Edits"')
    if len(rows[0]) >= 25: #para las gráficas de semanas, pero no para las de horas que se ven bien sin rotar
        gp('set xtics rotate by 90')
    gp('set xtics (%s)' % xtics.encode(smwconfig.preferences['codification']))
    c = 1
    plots = []
    for row in rows[1:]:
        plots.append(Gnuplot.PlotItems.Data(row, with_="boxes", title=headers[c].encode(smwconfig.preferences['codification'])))
        c += 1
    gp.plot(*plots)
    gp.hardcopy(filename=filename,terminal="png")
    gp.close()

def printGraphWorkDistribution(type, fileprefix, title, headers, rows):
    labels = ["Date (YYYY-MM-DD)", "Percent"]
    filename = "%s/graphs/%s/%s_work_distribution.png" % (smwconfig.preferences["outputDir"], type, fileprefix)
    printFilledcurvesGraph(title=title, filename=filename, labels=labels, headers=headers, rows=rows)

def printGraphContentEvolution(type, fileprefix, title, headers, rows):
    labels = ["Date (YYYY-MM-DD)", "Bytes"]
    filename = "%s/graphs/%s/%s_content_evolution.png" % (smwconfig.preferences["outputDir"], type, fileprefix)
    printLinesGraph(title=title, filename=filename, labels=labels, headers=headers, rows=rows)

def printGraphTimeActivity(type, fileprefix, title, headers, rows):
    filename = "%s/graphs/%s/%s_activity.png" % (smwconfig.preferences["outputDir"], type, fileprefix)
    printBarsGraph(title=title, filename=filename, headers=headers, rows=rows)
