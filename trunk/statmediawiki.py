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
import MySQLdb
import datetime
import re
import Gnuplot
import time
import md5

#variables
statsdir="statmediawiki"
#limpiamos directorio, realmente no debería limpiarlo, por si el usuario tenía ahí otra cosa
#os.system("rm -r %s" % statsdir)
sleep=0.8

indexfilename="index.html"
sitename="WikiHaskell"
siteurl=url="http://osl.uca.es/wikihaskell"
subdir="/index.php" # "/index.php"
dbname="wikihaskelldb"
tableprefix="" #generalmente vacío
fechainicio=datetime.datetime(year=2009, month=9, day=15, hour=0, minute=0, second=0)
#fechainicio=datetime.datetime(year=2007, month=1, day=1, hour=0, minute=0, second=0)
fechafin=datetime.datetime(year=2010, month=1, day=31, hour=0, minute=0, second=0)
fechaincremento=datetime.timedelta(days=1)

xtics24hours='"00" 0, "01" 1, "02" 2, "03" 3, "04" 4, "05" 5, "06" 6, "07" 7, "08" 8, "09" 9, "10" 10, "11" 11, "12" 12, "13" 13, "14" 14, "15" 15, "16" 16, "17" 17, "18" 18, "19" 19, "20" 20, "21" 21, "22" 22, "23" 23'
xticsdayofweek='"Monday" 0, "Tuesday" 1, "Wednesday" 2, "Thursday" 3, "Friday" 4, "Saturday" 5, "Sunday" 6'
#xticsperiod
fecha=fechainicio
xticsperiod=""
c=0
while fecha!=fechafin:
	if fecha.day in [1, 15]:
		xticsperiod+='"%s" %s,' % (fecha.strftime("%Y-%m-%d"), c)
	fecha+=fechaincremento
	c+=1
xticsperiod=xticsperiod[:len(xticsperiod)-1]

def header(title=""):
	return u"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es" dir="ltr">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
		<title>StatMediaWiki: %s %s</title>
		<style>
		body {
			margin-left: 42px;
			margin-right: 42px;
			background: #ffffff;
			color: #002070;
			font-family: Verdana, Arial, Helvetica, sans-serif;
			font-size: 12px;
		}
		h1 {
			padding: 2px 5px;
			border: 1px solid #c0c0c0;
			color: #002070;
			background-color: #eeeeee;
			font-weight: bold;
			font-size: 16px;
		}

		h2 {
			padding: 2px 5px;
			border: 1px solid #aaaaaa;
			color: #002070;
			background-color: #eeeeee;
			font-size: 14px;
		}

		table, td {
			border: 1px solid black;
			text-align: center;
		}
/*
estilo para los párrafos, tablas...
*/
		</style>
	</head>
	<body><h1>StatMediaWiki: %s %s</h1>
	""" % (sitename, title, sitename, title)

def footer():
	return u"<hr/>\n<center>Generated with <a href='http://statmediawiki.forja.rediris.es/'>StatMediaWiki</a></center>"

def subpageheader(subtitle, backlink=""):
	if not backlink:
		backlink=indexfilename
	return u"%s\n<p>&lt;&lt; <a href=\"%s\">Back</a></p>\n" % (header(subtitle), backlink)

def subpagefooter():
	return footer()


def generateCloud(revisions, user=""):
	cloud={}
	output=u""
	cloudmaxsize=50
	tagminsize=3
	exclusions=["las", "los", "con", "para", "que", "uno", "una", "del", "como"]
	for rev_id, rev_props in revisions.items():
		#print len(rev_props["rev_comment"])
		rev_user_text=rev_props["rev_user_text"]
		if user!="":
			if not user==rev_user_text:
				continue #saltamos a la siguiente revision
		rev_comment=rev_props["rev_comment"]
		rev_comment=rev_comment.lower()
		rev_comment=re.sub(ur"[^a-záéíóúñ0-9]", ur" ", rev_comment)
		tags=rev_comment.split(" ")
		for tag in tags:
			if len(tag)>=tagminsize and tag not in exclusions:
				if cloud.has_key(tag):
					cloud[tag]+=1
				else:
					cloud[tag]=1
	cloud_list=[]
	cloudfilename="cloud.html"
	if user!="":
		cloudfilename="user_%s_%s" % (users[user], cloudfilename)
	tagmin=999
	tagmax=0
	tagtotal=0.0
	for k, v in cloud.items():
		tagtotal+=v
		if v<tagmin:
			tagmin=v
		if v>tagmax:
			tagmax=v
		cloud_list.append([v, k])
	cloud_list.sort()
	cloud_list.reverse()
	cloud_list2=cloud_list
	cloud_list=[]
	for k, v in cloud_list2:
		cloud_list.append([v, k])
	if user!="":
		cloudfileoutput=subpageheader("Cloud: %s" % user, "user_%s.html" % users[user])
	else:
		cloudfileoutput=subpageheader("Cloud")
	cloudfileoutput+=u"<table><tr><th>Word</th><th>Frequency</th></tr>"
	for tag, times in cloud_list[:cloudmaxsize]:
		cloudfileoutput+=u"<tr><td>%s</td><td>%s (%.2f%%)</td></tr>\n" % (tag, times, times*(100/tagtotal))
	cloudfileoutput+=u"</table>"
	cloudfileoutput+=subpagefooter()
	cloudfile=open("%s/%s" % (statsdir, cloudfilename), "w")
	cloudfile.write(cloudfileoutput.encode("utf-8"))
	cloudfile.close()
	top_tags=cloud_list[:cloudmaxsize]
	top_tags.sort()
	fontsizemin=100
	fontsizemax=300
	try:
		multi=(fontsizemax-fontsizemin)/(tagmax-tagmin)
	except:
		multi=0
	for tag, times in top_tags:
		output+=u"<span style=\"font-size: %s%%\">%s</span> &nbsp;&nbsp;&nbsp;" % (fontsizemin+multi*times, tag)
	return output, cloudfilename

#inicialización
os.system("mkdir %s" % statsdir)

#conexión a la db
conn = MySQLdb.connect(host='localhost', db=dbname, read_default_file='~/.my.cnf', use_unicode=False)
cursor = conn.cursor()

#estadísticas globales
cursor.execute("select count(*) from %suser where 1" % tableprefix)
numberofusers=cursor.fetchall()[0][0]
cursor.execute("select count(*) from %srevision where 1" % tableprefix)
numberofedits=cursor.fetchall()[0][0]
cursor.execute("select count(*) from %srevision where rev_page in (select page_id from %spage where page_namespace=0)" % (tableprefix, tableprefix))
numberofeditsinarticles=cursor.fetchall()[0][0]
cursor.execute("select count(*) from %spage where 1" % tableprefix)
numberofpages=cursor.fetchall()[0][0]
cursor.execute("select count(*) from %spage where page_namespace=0 and page_is_redirect=0" % tableprefix)
numberofarticles=cursor.fetchall()[0][0]
cursor.execute("select sum(page_len) from %spage where 1" % tableprefix)
numberofbytes=cursor.fetchall()[0][0]
cursor.execute("select sum(page_len) from %spage where page_namespace=0 and page_is_redirect=0" % tableprefix)
numberofbytesinarticles=cursor.fetchall()[0][0]
cursor.execute("select count(*) from %simage where 1" % tableprefix)
numberoffiles=cursor.fetchall()[0][0]
generated=datetime.datetime.now().isoformat()
period="%s - %s" % (fechainicio.isoformat(), fechafin.isoformat())

#cargando datos

#pagenamespaces
namespaces={}
namespaces_={}

namespaces={0:u"",1:u"Talk",2:u"User",3:u"User talk", 4:u"Project", 5:u"Project talk", 6:u"File", 7:u"File talk", 8:u"MediaWiki", 9:u"MediaWiki talk", 10:u"Template", 11:u"Template talk", 12:u"Help", 13:u"Help talk", 14:u"Category", 15:u"Category talk"}
for k, v in namespaces.items():
	if v!="":
		namespaces_[k]=u"%s:" % v
	else:
		namespaces_[k]=u""

#pages
pages={}
cursor.execute("select page_id, page_namespace, page_title, page_is_redirect from %spage" % tableprefix)
result=cursor.fetchall()
for row in result:
	pages[row[0]]={"page_namespace": int(row[1]), "page_title": unicode(row[2], "utf-8"), "page_is_redirect": int(row[3])}
print "Loaded %s pages" % len(pages.items())

#revisions
revisions={}
cursor.execute("select rev_id, rev_page, rev_user_text, rev_timestamp, rev_comment, old_text from %srevision, %stext where old_id=rev_text_id" % (tableprefix, tableprefix))
result=cursor.fetchall()
for row in result:
	revisions[row[0]]={"rev_id": row[0], "rev_page":row[1], "rev_user_text": unicode(row[2], "utf-8"), 
"rev_timestamp": datetime.datetime(year=int(row[3][:4]), month=int(row[3][4:6]), day=int(row[3][6:8]), hour=int(row[3][8:10]), minute=int(row[3][10:12]), second=int(row[3][12:14])), "rev_comment": unicode(row[4].tostring(), "utf-8"), "old_text": unicode(row[5].tostring(), "utf-8")} #el rev_id no es un error
print "Loaded %s revisions" % len(revisions.items())

#organizamos revisions por páginas.simulando el historial
revisionsperpage={}
for rev_id, rev_props in revisions.items():
	if revisionsperpage.has_key(rev_props["rev_page"]):
		revisionsperpage[rev_props["rev_page"]].append([rev_props["rev_timestamp"], rev_props])
	else:
		#metemos edición dummy con texto=vacio y fecha prehistórica
		revisionsperpage[rev_props["rev_page"]]=[[datetime.datetime(year=1900, month=1, day=1), {"old_text":""}], [rev_props["rev_timestamp"], rev_props]]

#ordenamos historiales de cada página
for rev_page, hist in revisionsperpage.items():
	revisionsperpage[rev_page].sort()

#users
users={}
useruploads={}
cursor.execute("select user_name, user_id from %suser where 1" % tableprefix)
cursor.execute("select distinct rev_user_text, rev_user from %srevision where 1" % tableprefix)
result=cursor.fetchall()
for row in result:
	username=unicode(row[0], "utf-8")
	userid=int(row[1])
	if userid==0:
		users[username]=username
	else:
		users[username]=userid
	#inicializamos uploads
	useruploads[username]=[]

print "Loaded %s users" % len(users.items())

#user edits
useredits={}
usereditsinarticles={}
for rev_id, rev_props in revisions.items():
	username=rev_props["rev_user_text"]
	if useredits.has_key(username):
		useredits[username]+=1
	else:
		useredits[username]=1
	rev_page=rev_props["rev_page"]
	if not usereditsinarticles.has_key(username):
		usereditsinarticles[username]=0
	if pages[rev_page]["page_namespace"]==0:
		usereditsinarticles[username]+=1

#user page preferences
userpagepreferences={}
mosteditedpages={}
for rev_id, rev_props in revisions.items():
	username=rev_props["rev_user_text"]
	rev_page=rev_props["rev_page"]
	if not userpagepreferences.has_key(username):
		userpagepreferences[username]={}
	if userpagepreferences[username].has_key(rev_page):
		userpagepreferences[username][rev_page]+=1
	else:
		userpagepreferences[username][rev_page]=1
	if mosteditedpages.has_key(rev_page):
		mosteditedpages[rev_page]+=1
	else:
		mosteditedpages[rev_page]=1

#user uploads
cursor.execute("select img_user_text, img_name from %simage where 1" % tableprefix)
result=cursor.fetchall()
for row in result:
	username=unicode(row[0], "utf-8")
	imgname=unicode(row[1], "utf-8")
	useruploads[username].append(imgname)

#fin carga datos

#cabecera
output = header()
output+=u"""<dl>
<dt>Site:</dt>
<dd><a href='%s'>%s</a></dd>
<dt>Generated:</dt>
<dd>%s</dt>
<dt>Report period:</dt>
<dd>%s</dd>
<dt>Total pages:</dt>
<dd>%s (Articles: %s)</dd>
<dt>Total edits:</dt>
<dd>%s (In articles: %s)</dd>
<dt>Total bytes:</dt>
<dd>%s (In articles: %s)</dd>
<dt>Total files:</dt>
<dd><a href="%s%s/Special:Imagelist">%s</a></dd>
<dt>Users:</dt>
<dd><a href="users.html">%s</a></dd>
</dl>""" % (url, sitename, generated, period, numberofpages, numberofarticles, numberofedits, numberofeditsinarticles, numberofbytes, numberofbytesinarticles, url, subdir, numberoffiles, numberofusers)


output+=u"<h2>Content</h2>"
#gráfica evolución contenido global
fecha=fechainicio
graph1=[]
graph2=[]
c=0
while fecha<fechafin:
	status={}
	statusarticles={}
	for rev_id, rev_props in revisions.items():
		if rev_props["rev_timestamp"]<fecha and ((status.has_key(rev_props["rev_page"]) and status[rev_props["rev_page"]]["rev_timestamp"]<rev_props["rev_timestamp"]) or not status.has_key(rev_props["rev_page"])):
			status[rev_props["rev_page"]]=rev_props
	
	for rev_id, rev_props in revisions.items():
		if pages[rev_props["rev_page"]]["page_namespace"]==0 and rev_props["rev_timestamp"]<fecha and ((statusarticles.has_key(rev_props["rev_page"]) and statusarticles[rev_props["rev_page"]]["rev_timestamp"]<rev_props["rev_timestamp"]) or not statusarticles.has_key(rev_props["rev_page"])):
			statusarticles[rev_props["rev_page"]]=rev_props
	
	#recorremos entonces la instantanea de la wiki en aquel momento
	bytes=0
	for rev_page, rev_props in status.items():
		bytes+=len(rev_props["old_text"])
	graph1.append([c, bytes])
	
	bytesarticles=0
	for rev_page, rev_props in statusarticles.items():
		bytesarticles+=len(rev_props["old_text"])
	graph2.append([c, bytesarticles])
	c+=1
	fecha+=fechaincremento

gp = Gnuplot.Gnuplot()
gp("set data style lines")
gp('set title "Content evolution in %s"' % sitename)
gp('set xlabel "Date (YYYY-MM-DD)"')
gp('set ylabel "Bytes"')
gp('set xtics rotate by 90')
gp('set xtics (%s)' % xticsperiod)
plot1 = Gnuplot.PlotItems.Data(graph1, with_="lines", title="%s content (all pages)" % sitename)
plot2 = Gnuplot.PlotItems.Data(graph2, with_="lines", title="%s content (articles)" % sitename)
gp.plot(plot1, plot2)
gp.hardcopy(filename="%s/content_evolution.png" % statsdir,terminal="png") 

output+=u"<img src=\"%s\" />" % ("content_evolution.png")

houractivity={}
dayofweekactivity={}
#inicializamos horas del día
for i in range(24):
	houractivity[i]=0

#inicializamos días de la semana
for i in range(7):
	dayofweekactivity[i]=0

for rev_page, hist in revisionsperpage.items():
	c=0
	for rev_timestamp, rev_props in hist: #recorremos historial ordenado de más antiguo a más nuevo
		if c>0: #nos saltamos la revisión dummy
			#hour activity
			houractivity[rev_timestamp.hour]+=1
			#day of week activity
			dayofweekactivity[rev_timestamp.weekday()]+=1
		c+=1

#activity per hours
houractivity_list=houractivity.items()
houractivity_list.sort()
gp = Gnuplot.Gnuplot()
gp("set data style boxes")
gp('set title "Hour activity"')
gp('set xlabel "Hour"')
gp('set ylabel "Edits"')
gp('set xtics (%s)' % xtics24hours)
plottitle1=u"Edits"
plot1 = Gnuplot.PlotItems.Data(houractivity_list, with_="boxes", title=plottitle1.encode("utf-8"))
gp.plot(plot1)
gp.hardcopy(filename="%s/hour_activity.png" % (statsdir),terminal="png")
output+=u"<img src=\"hour_activity.png\"/>\n"

#activity day of week
dayofweekactivity_list=dayofweekactivity.items()
dayofweekactivity_list.sort()
gp = Gnuplot.Gnuplot()
gp("set data style boxes")
gp('set title "Day of week activity"')
gp('set xlabel "Day of week"')
gp('set ylabel "Edits"')
gp('set xtics (%s)' % xticsdayofweek)
plottitle1=u"Edits"
plot1 = Gnuplot.PlotItems.Data(dayofweekactivity_list, with_="boxes", title=plottitle1.encode("utf-8"))
gp.plot(plot1)
gp.hardcopy(filename="%s/dayofweek_activity.png" % (statsdir),terminal="png")
output+=u"<img src=\"dayofweek_activity.png\"/>\n"
#fin gráficas globales


#gráficas para todos los usuarios
#recorremos para cada usuario
usersbytes={}
usersbytesinarticles={}
for user, user_id in users.items():
	print user, user_id
	usersbytes[user]=0
	usersbytesinarticles[user]=0
	userbytes={} #user, not userS
	userbytesinarticles={}
	userhouractivity={}
	userdayofweekactivity={}
	fecha=fechainicio
	#inicializamos diccionario de fechas
	while fecha<fechafin:
		userbytes[fecha]=0
		userbytesinarticles[fecha]=0
		fecha+=fechaincremento
	#inicializamos horas del día
	for i in range(24):
		userhouractivity[i]=0
	#inicializamos días de la semana
	for i in range(7):
		userdayofweekactivity[i]=0

	for rev_page, hist in revisionsperpage.items():
		c=0
		for rev_timestamp, rev_props in hist: #recorremos historial ordenado de más antiguo a más nuevo
			if c>0: #nos saltamos la revisión dummy
				if rev_props["rev_user_text"]==user:
					diff=len(rev_props["old_text"])-len(hist[c-1][1]["old_text"])
					date=datetime.datetime(year=rev_timestamp.year, month=rev_timestamp.month, day=rev_timestamp.day, hour=0, minute=0, second=0)
					if diff>0:
						userbytes[date]+=diff
						usersbytes[user]+=diff
						if pages[rev_page]["page_namespace"]==0:
							userbytesinarticles[date]+=diff
							usersbytesinarticles[user]+=diff
					#user hour activity
					userhouractivity[rev_timestamp.hour]+=1
					#user day of week activity
					userdayofweekactivity[rev_timestamp.weekday()]+=1
			c+=1
	
	userbytes_list=[]
	userbytes_list2=[]
	for timestamp, bytes in userbytes.items():
		userbytes_list.append([timestamp, bytes])
	userbytes_list.sort()
	
	userbytesinarticles_list=[]
	userbytesinarticles_list2=[]
	for timestamp, bytes in userbytesinarticles.items():
		userbytesinarticles_list.append([timestamp, bytes])
	userbytesinarticles_list.sort()
	
	c=0
	acumbytes=0
	for timestamp, bytes in userbytes_list:
		acumbytes+=bytes #conservamos 
		userbytes_list2.append([c, acumbytes])
		c+=1
	
	c=0
	acumbytes=0
	for timestamp, bytes in userbytesinarticles_list:
		acumbytes+=bytes #conservamos 
		userbytesinarticles_list2.append([c, acumbytes])
		c+=1
	
	usersubpage=u"%s\n" % (subpageheader("Users: %s" % user))
	usersubpage+=u"""<dl>
<dt>User:</dt>
<dd><a href='%s%s/User:%s'>%s</a> (<a href='%s%s/Special:Contributions/%s'>contrib</a>)</dt>
<dt>Edits:</dt>
<dd>%s (In articles: %s)</dd>
<dt>Bytes added:</dt>
<dd>%s (In articles: %s)</dd>
<dt>Files uploaded:</dt>
<dd><a href="#uploads">%s</a></dd>
</dl>""" % (url, subdir, user, user, url, subdir, user, useredits[user], usereditsinarticles[user], usersbytes[user], usersbytesinarticles[user], len(useruploads[user]))
	
	#user content evolution
	if userbytes_list2:
		gp = Gnuplot.Gnuplot()
		gp("set data style lines")
		gp('set title "Content evolution by %s"' % user.encode("utf-8"))
		gp('set xlabel "Date (YYYY-MM-DD)"')
		gp('set ylabel "Bytes"')
		gp('set xtics rotate by 90')
		gp('set xtics (%s)' % xticsperiod)
		plottitle1=u"Content by %s (allpages)" % user
		plot1 = Gnuplot.PlotItems.Data(userbytes_list2, with_="lines", title=plottitle1.encode("utf-8"))
		plottitle2=u"Content by %s (articles)" % user
		plot2 = Gnuplot.PlotItems.Data(userbytesinarticles_list2, with_="lines", title=plottitle2.encode("utf-8"))
		gp.plot(plot1, plot2)
		gp.hardcopy(filename="%s/user_%s.png" % (statsdir, user_id),terminal="png")
		time.sleep(sleep) #para servidores quisquillosos como el nuestro
		#le creamos su subpagina
		
		
		usersubpage+=u"<img src=\"user_%s.png\"/>\n" % user_id
	
	#user activity per hours
	userhouractivity_list=userhouractivity.items()
	userhouractivity_list.sort()
	gp = Gnuplot.Gnuplot()
	gp("set data style boxes")
	gp('set title "Hour activity by %s"' % user.encode("utf-8"))
	gp('set xlabel "Hour"')
	gp('set ylabel "Edits"')
	gp('set xtics (%s)' % xtics24hours)
	plottitle1=u"Edits by %s" % user
	plot1 = Gnuplot.PlotItems.Data(userhouractivity_list, with_="boxes", title=plottitle1.encode("utf-8"))
	gp.plot(plot1)
	gp.hardcopy(filename="%s/user_%s_hour_activity.png" % (statsdir, user_id),terminal="png")
	usersubpage+=u"<img src=\"user_%s_hour_activity.png\"/>\n" % user_id
	
	#user activity day of week
	userdayofweekactivity_list=userdayofweekactivity.items()
	userdayofweekactivity_list.sort()
	gp = Gnuplot.Gnuplot()
	gp("set data style boxes")
	gp('set title "Day of week activity by %s"' % user.encode("utf-8"))
	gp('set xlabel "Day of week"')
	gp('set ylabel "Edits"')
	gp('set xtics (%s)' % xticsdayofweek)
	plottitle1=u"Edits by %s" % user
	plot1 = Gnuplot.PlotItems.Data(userdayofweekactivity_list, with_="boxes", title=plottitle1.encode("utf-8"))
	gp.plot(plot1)
	gp.hardcopy(filename="%s/user_%s_dayofweek_activity.png" % (statsdir, user_id),terminal="png")
	usersubpage+=u"<img src=\"user_%s_dayofweek_activity.png\"/>\n" % user_id
	
	#user most edited pages
	usersubpage+=u"<h2 id=''>Most edited pages</h2>\n"
	userpagepreferences_list=[]
	for k, v in userpagepreferences[user].items():
		userpagepreferences_list.append([v, k])
	userpagepreferences_list.sort()
	userpagepreferences_list.reverse()
	usersubpage+=u"<table>"
	usersubpage+=u"<tr><th>#</th><th>Page</th><th>Edits</th></tr>"
	c=0
	for edits, pageid in userpagepreferences_list:
		fullpagetitle=u"%s%s" % (namespaces_[pages[pageid]["page_namespace"]], pages[pageid]["page_title"])
		usersubpage+=u"<tr><td>%s</td><td><a href='%s%s/%s'>%s</a></td><td><a href='%s/index.php?title=%s&action=history'>%s</a></td></tr>\n" % (c, siteurl, subdir, fullpagetitle, fullpagetitle, siteurl, fullpagetitle, edits)
		c+=1
	usersubpage+=u"</table>"

	#user uploads
	usersubpage+=u"<h2 id='uploads'>Uploads</h2>\n"
	if len(useruploads[user])==0:
		usersubpage+=u"No files uploaded"
	else:
		for imgname in useruploads[user]:
			imgname_=re.sub(' ', '_', imgname) #espacios a _
			md5_=md5.md5(imgname_.encode('utf-8')).hexdigest() #digest hexadecimal
			usersubpage+=u"<a href='%s%s/Image:%s'><img src='%s/images/%s/%s/%s' width=200px /></a>&nbsp;&nbsp;&nbsp;" % (siteurl, subdir, imgname, siteurl, md5_[0], md5_[0:2], imgname) 

	#user cloud
	[cloud, cloudfilename]=generateCloud(revisions, user)
	usersubpage+=u"<h2>Cloud</h2>%s<p><a href=\"%s\">more...</a></p>\n" % (cloud, cloudfilename)
	
	usersubpage+=subpagefooter()
	
	f=open("%s/user_%s.html" % (statsdir, user_id), "w")
	f.write(usersubpage.encode("utf-8"))
	f.close()
#fin gráficas para usuarios


output+=u"<h2>Users</h2>"
#los 10 primeros users
output+=u"<table>"

usersmaxsize=10
usersmaxsize2=10000 #todos deben salir en la subpagina
users_list=[]
usersfilename="users.html"
editsmin=999
editsmax=0
#edits
editstotal=0.0
for k, v in useredits.items():
	editstotal+=v
	if v<editsmin:
		editsmin=v
	if v>editsmax:
		editsmax=v
	users_list.append([v, k])
editstotalinarticles=0.0
for k, v in usereditsinarticles.items():
	editstotalinarticles+=v
#bytes
bytesaddedtotal=0.0
for k, v in usersbytes.items():
	bytesaddedtotal+=v
bytesaddedinarticlestotal=0.0
for k, v in usersbytesinarticles.items():
	bytesaddedinarticlestotal+=v

#uploads
totaluploads=0.0
for k, v in useruploads.items():
	totaluploads+=len(useruploads[k])

users_list.sort()
users_list.reverse()
users_list2=users_list
users_list=[]
for k, v in users_list2:
	users_list.append([v, k])
usersfileoutput=subpageheader("Users")
usersfileoutput+="""<dl>
<dt>Number of users:</dt>
<dd>%s</dt>
</dl>""" % len(users.items())
usersfileoutput+=u"<table><tr><th>#</th><th>User</th><th>Total edits</th><th>Edits in articles</th><th>Total bytes added</th><th>Bytes added in articles</th><th>Uploads</th></tr>"
c=1
for username, edits in users_list[:usersmaxsize2]:
	usersfileoutput+=u"<tr><td>%s</td><td><a href=\"user_%s.html\">%s</a></td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s</td></tr>\n" % (c, users[username], username, edits, edits*(100/editstotal), usereditsinarticles[username], usereditsinarticles[username]*(100/editstotalinarticles), usersbytes[username], usersbytes[username]*(100/bytesaddedtotal), usersbytesinarticles[username], usersbytesinarticles[username]*(100/bytesaddedinarticlestotal), len(useruploads[username]))
	c+=1
usersfileoutput+=u"<tr><td></td><td>Total</td><td>%s (100%%)</td><td>%s (100%%)</td><td>%s<sup>[<a href='#note 1'>note 1</a>]</sup> (100%%)</td><td>%s (100%%)</td><td>%.0f</td></tr>\n" % (editstotal, editstotalinarticles, bytesaddedtotal, bytesaddedinarticlestotal, totaluploads)
usersfileoutput+=u"</table>"
usersfileoutput+=u"<h2>Notes</h2>\n<ul><li id='note 1'>Note 1: This number can be greater than total bytes in the wiki, as some of the content inserted could have been deleted later.</li>"
usersfileoutput+=subpagefooter()
usersfile=open("%s/%s" % (statsdir, usersfilename), "w")
usersfile.write(usersfileoutput.encode("utf-8"))
usersfile.close()
top_users=users_list[:usersmaxsize]
#top_users.sort()
output+=u"<table><tr><th>#</th><th>User</th><th>Total edits</th><th>Edits in articles</th><th>Total bytes added</th><th>Bytes added in articles</th><th>Uploads</th></tr>"
subtotaledits=0.0
subtotaleditsinarticles=0.0
subtotalbytesadded=0.0
subtotalbytesaddedinarticles=0.0
subtotaluploads=0.0
c=1
for username, edits in top_users:
	subtotaledits+=edits
	subtotaleditsinarticles+=usereditsinarticles[username]
	subtotalbytesadded+=usersbytes[username]
	subtotalbytesaddedinarticles+=usersbytesinarticles[username]
	subtotaluploads+=len(useruploads[username])
	output+=u"<tr><td>%s</td><td><a href=\"user_%s.html\">%s</a></td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s</td></tr>\n" % (c, users[username], username, edits, edits*(100/editstotal), usereditsinarticles[username], usereditsinarticles[username]*(100/editstotalinarticles), usersbytes[username], usersbytes[username]*(100/bytesaddedtotal), usersbytesinarticles[username], usersbytesinarticles[username]*(100/bytesaddedinarticlestotal), len(useruploads[username]))
	c+=1

output+=u"<tr><td></td><td>Subtotal</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%s (%.2f%%)</td><td>%.0f</td></tr>\n" % (subtotaledits, subtotaledits*(100/editstotal), subtotaleditsinarticles, subtotaleditsinarticles*(100/editstotalinarticles), subtotalbytesadded, subtotalbytesadded*(100/bytesaddedtotal), subtotalbytesaddedinarticles, subtotalbytesaddedinarticles*(100/bytesaddedinarticlestotal), subtotaluploads)
	

output+=u"</table>"

output+=u"<p><a href=\"%s\">more...</a></p>" % (usersfilename)

#most edited pages
mosteditedpages_list=[]
for pageid, edits in mosteditedpages.items():
	mosteditedpages_list.append([edits, pageid])
mosteditedpages_list.sort()
mosteditedpages_list.reverse()
c=1
output+=u"<h2>Most edited pages</h2>\n"
output+=u"<table><tr><th>#</th><th>Page</th><th>Edits</th></tr>"
mosteditedoutput=subpageheader("Most edited pages")
mosteditedoutput+=u"<table><tr><th>#</th><th>Page</th><th>Edits</th></tr>"
for edits, pageid in mosteditedpages_list:
	fullpagetitle=u"%s%s" % (namespaces_[pages[pageid]["page_namespace"]], pages[pageid]["page_title"])
	if c<=10:		
		output+=u"<tr><td>%s</td><td><a href='%s%s/%s'>%s</a></td><td><a href='%s/index.php?title=%s&action=history'>%s</a></td></tr>\n" % (c, siteurl, subdir, fullpagetitle, fullpagetitle,  siteurl, fullpagetitle, edits)
	mosteditedoutput+=u"<tr><td>%s</td><td><a href='%s%s/%s'>%s</a></td><td><a href='%s/index.php?title=%s&action=history'>%s</a></td></tr>\n" % (c, siteurl, subdir, fullpagetitle, fullpagetitle,  siteurl, fullpagetitle, edits)
	c+=1
output+=u"</table>"
output+=u"<p><a href=\"mosteditedpages.html\">more...</a></p>"
mosteditedoutput+=u"</table>"
f=open("%s/%s" % (statsdir,"mosteditedpages.html"), "w")
f.write(mosteditedoutput.encode("utf-8"))
f.close()


#cloud
output+=u"<h2>Tags cloud of words in edit comments</h2>"
[cloud, cloudfilename]=generateCloud(revisions)
output+=cloud
output+=u"<p><a href=\"%s\">more...</a></p>" % (cloudfilename)

#footer
output+=footer()

"""

#ranking ediciones globales
cursor.execute("select user_name, user_editcount from %suser where 1 order by user_editcount desc" % tableprefix)
result=cursor.fetchall()
output+=u"<h2>Ranking de usuarios por número de ediciones globales</h2>"
output+=u"<center>\n<table style='text-align: center;font-size: 90%;' border=1px>\n<tr><th>#</th><th>Usuario</th><th>Ediciones</th><th>Detalles</th></tr>\n"
c=1
user_names=[]
for row in result:
	user_name=unicode(row[0], "utf-8")
	user_editcount=row[1]
	user_names.append(user_name)
	output+=u"<tr><td>%s</td><td><a href='%s%s/User:%s'>%s</a></td><td><a href='%s%s/Special:Contributions/%s'>%s</a></td><td><a href='#%s'>Ver</a></td></tr>\n" % (c, url, subdir, user_name, user_name, url, subdir, user_name, user_editcount, user_name)
	c+=1
output+=u"</table>\n</center>\n"

#detalles de cada usuario
for user_name in user_names:
	fecha=fechainicio
	output+=u"<h3 id='%s'>Detalles de \"%s\"</h3>\n" % (user_name, user_name)
	cursor.execute("select rev_id, rev_timestamp from %srevision where rev_user_text='%s'" % (user_name.encode("utf-8"), tableprefix))
	result=cursor.fetchall()
	user_revs={}
	while fecha!=fechafin:
		user_revs[fecha]=[]
		fecha+=fechaincremento
	c=0
	for row in result:
		c+=1
		rev_id="%s" % row[0]
		rev_timestamp=unicode(row[1], "utf-8")
		[y, m, d]=[int(rev_timestamp[0:4]), int(rev_timestamp[4:6]), int(rev_timestamp[6:8])]
		user_revs[datetime.date(year=y, month=m, day=d)].append(rev_id)
		#rev_comment=unicode(row[1], "utf-8")
		#output+=u"%s [%s]\n" % (rev_id, rev_comment)
	output+=u"Este usuario ha realizado %s cambios en %s" % (c, sitename)
	fecha=fechainicio
	nada=False
	while fecha!=fechafin:
		if len(user_revs[fecha])==0:
			if not nada:
				output+=u"<li>Nada</li>"
				nada=True
		else:
			#20091118063509&limit=20&target=TocinoCollantesJoseMaria&title=Especial%3AContributions&namespace=0
			offset="%s235959" % re.sub("-", "", fecha.isoformat())
			output+=u"<li><a href=\"%s%s?offset=%s&limit=%s&target=%s&title=Special:Contributions\">%s</a>: %s</li>" % (url, subdir, offset, len(user_revs[fecha]), user_name, fecha.isoformat(), ", ".join(user_revs[fecha]))
			nada=False
		fecha+=incremento
"""

#almacenar fichero estadísticas
f=open("%s/%s" % (statsdir, indexfilename), "w")
f.write(output.encode("utf-8"))
f.close()



