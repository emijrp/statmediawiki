#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2012 StatMediaWiki
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

import numpy
import pylab

import smwsummary

def pareto(cursor=None, title=''):
    totaledits = smwsummary.totalEdits(cursor=cursor)
    totalusers = smwsummary.totalUsers(cursor=cursor)

    result = cursor.execute("SELECT user_editcount FROM user WHERE 1 ORDER BY user_editcount DESC")

    x = []
    x2 = []
    edits = 0
    edits2 = 0
    users = 0
    split = 20.0 # 10, 100 percent
    for row in result:
        edits += row[0]
        edits2 += row[0]
        users += 1
        if users >= totalusers/split:
            x.append(edits/(totaledits/split))
            x2.append(edits2/(totaledits/split))
            users = 0
            edits2 = 0
    x.append(edits/(totaledits/split))
    x2.append(edits2/(totaledits/split))

    fig = pylab.figure()
    subfig = fig.add_subplot(1,1,1)

    subfig.plot(x, color='#1155ff')
    rects = subfig.bar(numpy.arange(len(x2)), x2, color='#ff33aa')
    subfig.set_xlabel('Users (%)')
    subfig.set_xticks(numpy.arange(len(x)))
    subfig.set_xticklabels([i for i in range(100, int(100/split))])
    subfig.set_ylabel('Edits (%)')

    maxheight = max([rect.get_height() for rect in rects])
    for rect in rects:
        height = rect.get_height()
        subfig.text(rect.get_x()+rect.get_width()/2., height+(maxheight/50), str(height), ha='center', va='bottom')

