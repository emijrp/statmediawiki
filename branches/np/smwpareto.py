# -*- coding: utf-8  -*-

import numpy
import pylab

def pareto(cursor=None, title=''):
    
    a = cursor.execute("select count(*) as count from revision where 1 group by username order by count desc")
    
    x = []
    acum = []
    c = 0
    for row in a:
        x.append(row[0])
        c += row[0]
        acum.append(c)
    
    pylab.plot(x)
    pylab.plot(acum)
    pylab.show()
