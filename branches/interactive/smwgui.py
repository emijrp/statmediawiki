#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2011 StatMediaWiki
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
import platform
import sqlite3
import thread
import webbrowser

from Tkinter import *
import tkMessageBox
import tkSimpleDialog
import tkFileDialog
import pylab

# Dependences:
# linux: python, python-tk, python-matplotlib
# windows: (mirar correo que envié a manolo explicando como probarlo en windows)

# TODO:
# indicar % progreso al parsear el dump, en función de una estimación por el tamaño del fichero (depende si es 7z, bzip, etc [leer tamaño del .xml comprimido directamente si es posible])
# cargar todos los dumps de wikiteam (cuando hay más de 100 en google code, solo salen los más recientes), mostrar progreso también
# almacenar sesiones o algo parecido para evitar tener que darle a preprocessing para que coja el proyecto, cada vez que arranca el programa
## pero al final tienes que carga la sesión/workplace que te interese, estamos en las mismas
# corregir todas las rutas relativas y hacerlas bien (donde se guardan los dumps, los .dbs, etc)
# capturar parámetros por si se quiere ejecutar sin gui desde consola: smwgui.py --module=summary invalida la gui y muestra los datos por consola
# hacer un listbox para los proyectos de wikimedia y wikia (almacenar en una tabla en un sqlite propia de smw? y actualizar cada poco?) http://download.wikimedia.org/backup-index.html http://community.wikia.com/wiki/Hub:Big_wikis http://community.wikia.com/index.php?title=Special:Newwikis&dir=prev&limit=500&showall=0 http://www.mediawiki.org/wiki/Sites_using_MediaWiki
# Citizendium (interesantes gráficas http://en.citizendium.org/wiki/CZ:Statistics) no publican el historial completo, solo el current http://en.citizendium.org/wiki/CZ:Downloads
# permitir descargar solo el historial de una página (special:Export tiene la pega de que solo muestra las últimas 1000 ediciones), con la Api te traes todo en bloques de 500 pero hay que hacer una función que llame a la API (en vez de utilizar pywikipediabot para no añadir una dependencia más)
# permitir descargar todos los dumps en lote, y luego preprocesarlos
# hay otros dumps a parte de los 7z que tienen información útil, por ejemplo los images.sql con metadatos de las fotos, aunque solo los publica wikipedia
# usar getopt para capturar parámetros desde consola
# i18n http://www.learningpython.com/2006/12/03/translating-your-pythonpygtk-application/
# write documentation

#diferenciar entre activity (edits) y newpages

# Ideas para análisis de wikis:
# * reverts rate: ratio de reversiones (como de eficiente es la comunidad)
# * ip geolocation: http://software77.net/geo-ip/?license
# * análisis que permita buscar ciertas palabras en los comentarios de las ediciones
# * mensajes entre usuarios (ediciones de usuarios en user talk:)
# * calcular autoría por páginas (colorear el texto actual?)
#
# Ideas para otros análisis que no usan dumps pero relacionados con wikis o wikipedia:
# * el feed de donaciones
# * log de visitas de domas?
# * conectarse a irc y poder hacer estadisticas en vivo?
#
# embeber mejor las gráficas en Tk? http://matplotlib.sourceforge.net/examples/user_interfaces/embedding_in_tk.py así cuando se cierra SMW, se cerrarán las gráficas; sería hacer una clase como listbox, a la que se le pasa la figura f (las funciones que generan las gráficas deberían devolver la f, ahora no devuelven nada)
#
# otras ideas:
# * mirar http://stats.wikimedia.org/reportcard/RC_2011_04_columns.html http://stats.wikimedia.org/reportcard/
# * exporter: ventana que marcando los items (registros de la bbdd) que te interesa, los exporta desde la bbdd hacia un CSV u otros formatos, exportar un rango de fechas de revisiones http://en.wikipedia.org/w/index.php?title=User_talk:Emijrp/Wikipedia_Archive&oldid=399534070#How_can_i_get_all_the_revisions_of_a_language_for_a_duration_.3F
# * al exportar con CSV podemos pasarle MINE
# * necesidades de los investigadores http://www.mediawiki.org/wiki/Research_Data_Proposals
# * external links analysis: http://linkypedia.inkdroid.org/websites/9/users/
# que es más seguro hacer las cursor.execute, con ? o con %s ?
# 
# flipadas:
# * ampliar la información de un punto haciendo clic en él: http://matplotlib.sourceforge.net/examples/event_handling/data_browser.py
# * videos con matplotlib http://matplotlib.sourceforge.net/examples/animation/movie_demo.py
# * más ejemplos de matplotlib http://matplotlib.sourceforge.net/examples/index.html
# * mapas con R muy buenos http://flowingdata.com/2011/05/11/how-to-map-connections-with-great-circles/ http://www.webcitation.org/5zuFPrssa
#
# dispenser coord dumps: http://toolserver.org/~dispenser/dumps/

NAME = 'StatMediaWiki Interactive' # StatMediaWiki name
VERSION = '0.1.4' # StatMediaWiki version
HOMEPAGE = 'http://statmediawiki.forja.rediris.es/index_en.html' # StatMediaWiki homepage
LINUX = platform.system().lower() == 'linux'
PATH = os.path.dirname(__file__)
if PATH: os.chdir(PATH)

class DialogListbox(Toplevel):
    #Following this tutorial http://effbot.org/tkinterbook/tkinter-dialog-windows.htm
    def __init__(self, parent, title = None, list = []):
        Toplevel.__init__(self, parent)
        self.transient = parent
        self.title = title
        self.parent = parent
        self.list = list
        self.result = None

        body = Frame(self)
        body.grid(row=0, column=0)
        self.listbox()
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry('300x550')
        self.wait_window(self)

    def listbox(self):
        box = Frame(self)

        scrollbar = Scrollbar(box)
        scrollbar.grid(row=0, column=2, sticky=N+S)
        self.listbox = Listbox(box, width=35, height=31)
        self.listbox.grid(row=0, column=0, columnspan=2, sticky=W)
        [self.listbox.insert(END, item) for item in self.list]
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        w1 = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w1.grid(row=1, column=0, sticky=W)
        w2 = Button(box, text="Cancel", width=10, command=self.cancel)
        w2.grid(row=1, column=1, sticky=E)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def apply(self):
        self.result = self.list[int(self.listbox.curselection()[0])]

class App:
    def __init__(self, master):
        self.master = master
        self.site = ''
        self.wiki = ''
        self.dbfilename = '' # current analysis

        # interface elements
        #description
        self.desc = Label(self.master, text="%s (version %s)\nThis program is free software (GPL v3 or higher)" % (NAME, VERSION), font=("Arial", 7))
        self.desc.grid(row=2, column=1, columnspan=2)
        #quick buttons
        self.button1 = Button(self.master, text="Load", command=self.loadDBFilename, width=12)
        self.button1.grid(row=0, column=1)
        self.button2 = Button(self.master, text="Button #2", command=self.callback, width=12)
        self.button2.grid(row=1, column=1)
        self.button3 = Button(self.master, text="Button #3", command=self.callback, width=12)
        self.button3.grid(row=0, column=2)
        self.button4 = Button(self.master, text="Exit", command=askclose, width=12)
        self.button4.grid(row=1, column=2)
        #statusbar
        self.status = Label(self.master, text="Welcome! %s is ready for work" % (NAME), bd=1, justify=LEFT, relief=SUNKEN)
        self.status.grid(row=3, column=0, columnspan=3, sticky=W+E)
        #self.status.config(text="AA")

        #create a menu
        menu = Menu(self.master)
        master.config(menu=menu)

        #begin file
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Preferences", command=self.callback)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=askclose)
        #end file

        #begin downloader
        downloadermenu = Menu(menu)
        menu.add_cascade(label="Downloader", menu=downloadermenu)
        downloadermywikimenu = Menu(downloadermenu)
        downloadermenu.add_command(label="My wiki", command=lambda: self.downloader('mywiki'))
        wikimediamenu = Menu(downloadermenu)
        downloadermenu.add_cascade(label="Wikimedia", menu=wikimediamenu)
        wikimediamenu.add_command(label="Full XML dump", command=lambda: self.downloader('wikimedia'))
        #http://en.wikipedia.org/w/api.php?action=sitematrix
        wikimediamenu.add_command(label="Pages subset", command=lambda: self.callback)
        wikimediamenu.add_command(label="Users subset", command=lambda: self.callback)
        #users in a cat,
        #get usercontribs and later...
        #retrieve batch revs (prop=revisions)
        #http://en.wikipedia.org/w/api.php?action=query&prop=revisions&revids=5555|6666|7777|8988|9999|10000|553|4345345|32534|98394|98349|9384|398489|300940|93843|0929|0303&rvprop=ids|timestamp|user|comment|content|size
        #hay un problema: no hay información sobre la revprev y la revnext, para calcular incrementos en bytes respecto a la rev anterior
        #además, al cargar solo un subconjunto de usuarios (un subcojunto de las rev totales del wiki), los historiales de las páginas no serían reales
        #y habría grandes lagunas a la hora de calcular cosas habría uqe tener cuidado de no confundir
        #si consigo sacar el len(rev_prev) y meter el incremento (positivo o negativo) como rev_diff_len, entonces ok
        
        downloadermenu.add_command(label="Wikia", command=lambda: self.downloader('wikia'))
        downloadermenu.add_command(label="WikiTeam", command=lambda: self.downloader('wikiteam'))
        downloadermenu.add_command(label="Citizendium", command=lambda: self.downloader('citizendium'))
        #end downloader

        #begin preprocessor
        preprocessormenu = Menu(menu)
        menu.add_cascade(label="Preprocessor", menu=preprocessormenu)
        preprocessormenu.add_command(label="XML dump", command=lambda: self.parser())
        #end preprocessor

        #begin analyser
        analysismenu = Menu(menu)
        menu.add_cascade(label="Analyser", menu=analysismenu)

        #begin global
        globalmenu = Menu(analysismenu)
        analysismenu.add_cascade(label="Global", menu=globalmenu)
        globalmenu.add_command(label="Summary", command=lambda: self.analysis('global-summary'))
        #begin activity
        globalactivitymenu = Menu(globalmenu)
        globalmenu.add_cascade(label="Activity", menu=globalactivitymenu)
        globalactivitymenu.add_command(label="All", command=lambda: self.analysis('global-activity-all'))
        globalactivitymenu.add_separator()
        globalactivitymenu.add_command(label="Yearly", command=lambda: self.analysis('global-activity-yearly'))
        globalactivitymenu.add_command(label="Monthly", command=lambda: self.analysis('global-activity-monthly'))
        #fix: weekly (~50 weeks)
        globalactivitymenu.add_command(label="Day of week", command=lambda: self.analysis('global-activity-dow'))
        globalactivitymenu.add_command(label="Hourly", command=lambda: self.analysis('global-activity-hourly'))
        #end activity
        globalmenu.add_command(label="GeoIP location", command=lambda: self.analysis('global-geoiplocation'))
        globalmenu.add_command(label="Pareto", command=lambda: self.analysis('global-pareto'))
        #end global

        #begin user-by-user
        userbyusermenu = Menu(analysismenu)
        analysismenu.add_cascade(label="User-by-user", menu=userbyusermenu)
        useractivitymenu = Menu(userbyusermenu)
        userbyusermenu.add_cascade(label="Activity", menu=useractivitymenu)
        useractivitymenu.add_command(label="All", command=lambda: self.analysis('user-activity-all'))
        useractivitymenu.add_separator()
        useractivitymenu.add_command(label="Yearly", command=lambda: self.analysis('user-activity-yearly'))
        useractivitymenu.add_command(label="Monthly", command=lambda: self.analysis('user-activity-monthly'))
        useractivitymenu.add_command(label="Day of week", command=lambda: self.analysis('user-activity-dow'))
        useractivitymenu.add_command(label="Hourly", command=lambda: self.analysis('user-activity-hourly'))

        #usergraphsmenu = Menu(userbyusermenu)
        #userbyusermenu.add_cascade(label="Graphs", menu=usergraphsmenu)
        #usergraphsmenu.add_command(label="Edited pages", command=lambda: self.analysis('user-graph'))
        #end user-by-user

        #begin page-by-page
        pagebypagemenu = Menu(analysismenu)
        analysismenu.add_cascade(label="Page-by-page", menu=pagebypagemenu)
        pageactivitymenu = Menu(pagebypagemenu)
        pagebypagemenu.add_cascade(label="Activity", menu=pageactivitymenu)
        pageactivitymenu.add_command(label="All", command=lambda: self.analysis('page-activity-all'))
        pageactivitymenu.add_separator()
        pageactivitymenu.add_command(label="Yearly", command=lambda: self.analysis('page-activity-yearly'))
        pageactivitymenu.add_command(label="Monthly", command=lambda: self.analysis('page-activity-monthly'))
        pageactivitymenu.add_command(label="Day of week", command=lambda: self.analysis('pager-activity-dow'))
        pageactivitymenu.add_command(label="Hourly", command=lambda: self.analysis('page-activity-hourly'))

        pagebypagemenu.add_command(label="Edit history graph", command=lambda: self.analysis('page-edithistorygraph'))
        pagebypagemenu.add_command(label="GeoIP location", command=lambda: self.analysis('page-geoiplocation'))

        #end page-by-page
        
        #begin samples
        samplesmenu = Menu(analysismenu)
        analysismenu.add_cascade(label="Samples", menu=samplesmenu)
        samplescategorymenu = Menu(samplesmenu)
        samplesmenu.add_cascade(label="Category", menu=samplescategorymenu)
        samplesdaterangemenu = Menu(samplesmenu)
        samplesmenu.add_cascade(label="Date range", menu=samplescategorymenu)
        samplesrandommenu = Menu(samplesmenu)
        samplesmenu.add_cascade(label="Random sample", menu=samplesrandommenu)
        sampleswikiprojectmenu = Menu(samplesmenu)
        samplesmenu.add_cascade(label="Wikiproject", menu=sampleswikiprojectmenu)
        
        #end samples
        
        analysismenu.add_command(label="Reverts evolution", command=lambda: self.analysis('reverts'))
        analysismenu.add_command(label="Newpages evolution", command=lambda: self.analysis('newpages'))
        analysismenu.add_command(label="Newusers evolution", command=lambda: self.analysis('newusers'))
        analysismenu.add_command(label="User messages graph", command=lambda: self.analysis('graph-user-messages'))
        analysismenu.add_command(label="User edits network", command=lambda: self.analysis('graph-user-edits-network'))
        
        #end analyser
        
        #begin others
        othermenu = Menu(menu)
        menu.add_cascade(label="Other", menu=othermenu)
        othermenu.add_command(label="Domas visits logs", command=self.callback)
        othermenu.add_command(label="Wikimedia Fundraising", command=self.callback)
        #end others

        #begin view
        viewmenu = Menu(menu)
        menu.add_cascade(label="View", menu=viewmenu)
        viewmenu.add_command(label="Console", command=self.callback)
        #end view

        #help
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About", command=self.callback)
        helpmenu.add_command(label="Help index", command=self.callback)
        helpmenu.add_command(label="StatMediaWiki homepage", command=lambda: webbrowser.open_new_tab(HOMEPAGE))

    def callback(self):
        self.setStatus("Feature not implemented for the moment. Contributions are welcome.")

    def setStatus(self, text):
        self.status.config(text=text)
        print text

    def loadDBFilename(self):
        initialdir = 'dumps/sqlitedbs'
        if PATH:
            initialdir = '%s/%s' % (PATH, initialdir)
        self.dbfilename = tkFileDialog.askopenfilename(initialdir=initialdir)
        self.setStatus("Loaded %s" % (self.dbfilename.split('/')[-1]))
        self.wiki = self.dbfilename.split('/')[-1]

    def downloader(self, site):
        import smwdownloader

        self.site = site
        self.wiki = ''
        initialdir = 'dumps'
        dumpfilename = ''
        if self.site == 'mywiki':
            initialvalue = "http://mywiki.com/w/api.php"
            apiurl = tkSimpleDialog.askstring("What is the API url?", "Put an url", initialvalue=initialvalue)
            if apiurl != initialvalue:
                self.wiki = apiurl
                #dumpfilename = '%s-latest-pages-meta-history.xml.7z' % (self.wiki)
                dumpfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir, initialfile='', defaultextension='')
        elif self.site == 'wikimedia':
            self.setStatus("Loading list of Wikimedia wikis")
            list = smwdownloader.downloadWikimediaList()
            self.setStatus("Loaded list of Wikimedia wikis")
            d = DialogListbox(self.master, title='Select a Wikimedia project', list=list)
            if d.result:
                self.wiki = d.result
                dumpfilename = '%s-latest-pages-meta-history.xml.7z' % (self.wiki)
                dumpfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir, initialfile=dumpfilename, defaultextension='.xml.7z')
        elif self.site == 'wikia':
            self.setStatus("Loading list of Wikia wikis")
            list = smwdownloader.downloadWikiaList()
            self.setStatus("Loaded list of Wikia wikis")
            d = DialogListbox(self.master, title='Select a Wikia project', list=list)
            if d.result:
                self.wiki = d.result
                dumpfilename = '%s-pages_full.xml.gz' % (self.wiki)
                dumpfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir, initialfile=dumpfilename, defaultextension='.xml.gz')
        elif self.site == 'wikiteam':
            self.setStatus("Loading list of WikiTeam wikis")
            list = smwdownloader.downloadWikiTeamList()
            self.setStatus("Loaded list of WikiTeam wikis")
            d = DialogListbox(self.master, title='Select a WikiTeam project', list=list)
            if d.result:
                self.wiki = d.result
                dumpfilename = '%s-history.xml.7z' % (self.wiki)
                dumpfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir, initialfile=dumpfilename, defaultextension='.xml.7z')
        elif self.site == 'citizendium':
            self.wiki = 'cz'
            #http://locke.citizendium.org/download/cz.dump.current.xml.gz
            #todo también tiene uno en bz2 http://locke.citizendium.org/download/cz.dump.current.xml.bz2
            dumpfilename = '%s.dump.current.xml.gz' % (self.wiki)
            dumpfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir, initialfile=dumpfilename, defaultextension='.xml.gz')

        if self.wiki and dumpfilename:
            self.setStatus("Downloading data for %s @ %s" % (self.wiki, self.site))
            if self.site == 'mywiki':
                smwdownloader.downloadMyWikiDump(self.wiki, dumpfilename)
            elif self.site == 'wikimedia':
                smwdownloader.downloadWikimediaDump(self.wiki, dumpfilename)
            elif self.site == 'wikia':
                smwdownloader.downloadWikiaDump(self.wiki, dumpfilename)
            elif self.site == 'wikiteam':
                smwdownloader.downloadWikiTeamDump(self.wiki, dumpfilename)
            elif self.site == 'citizendium':
                smwdownloader.downloadCitizendiumDump(self.wiki, dumpfilename)
            self.setStatus("Downloaded data for %s @ %s OK!" % (self.wiki, self.site))

    def parser(self):
        import smwparser

        initialdir = 'dumps'
        initialdir2 = 'dumps/sqlitedbs'
        dumpfilename = ''
        self.dbfilename = ''

        dumpfilename = tkFileDialog.askopenfilename(initialdir=initialdir, initialfile='', filetypes=[('XML', '*.xml'), ('7zip', '*.7z'), ('Gzip', '*.gz')])
        initialfile = '%s.db' % (dumpfilename.split('/')[-1].split('.xml')[0])
        self.dbfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir2, initialfile=initialfile, filetypes=[('SQLite3', '*.db')])

        if dumpfilename and self.dbfilename:
            dumpfilename2 = dumpfilename.split('/')[-1]
            self.setStatus("Parsing %s" % (dumpfilename2))
            smwparser.parseMediaWikiXMLDump(dumpfilename=dumpfilename, dbfilename=self.dbfilename)
            #tkMessageBox.showinfo("OK", "Parsing complete")
            self.setStatus("Parsed %s OK!" % (dumpfilename2))
        else:
            self.setStatus("ERROR: NO DUMP FILENAME OR NO DB FILENAME")

    def analysis(self, analysis):
        if not self.dbfilename:
            message = "You must load a preprocessed dump first"
            self.setStatus(message)
            tkMessageBox.showerror("Error", message)
            return

        conn = sqlite3.connect(self.dbfilename)
        cursor = conn.cursor()

        #global
        if analysis.startswith('global'):
            if analysis == 'global-summary':
                import smwsummary
                smwsummary.summary(cursor=cursor)
            elif analysis.startswith('global-activity'):
                import smwactivity
                if analysis == 'global-activity-all':
                    smwactivity.activityall(cursor=cursor, range='global', title=self.wiki)
                elif analysis == 'global-activity-yearly':
                    smwactivity.activityyearly(cursor=cursor, range='global', title=self.wiki)
                elif analysis == 'global-activity-monthly':
                    smwactivity.activitymonthly(cursor=cursor, range='global', title=self.wiki)
                elif analysis == 'global-activity-dow':
                    smwactivity.activitydow(cursor=cursor, range='global', title=self.wiki)
                elif analysis == 'global-activity-hourly':
                    smwactivity.activityhourly(cursor=cursor, range='global', title=self.wiki)
                pylab.show()
            elif analysis == 'global-geoiplocation':
                import smwgeolocation
                smwgeolocation.GeoLocationGraph(cursor=cursor, range='global', title=self.wiki)
                pylab.show()
            elif analysis == 'global-pareto':
                import smwpareto
                smwpareto.pareto(cursor=cursor, title=self.wiki)
                pylab.show()
        #user
        elif analysis.startswith('user'):
            import smwlist
            list = smwlist.listofusers(cursor=cursor)
            d = DialogListbox(self.master, title="AAA", list=list)
            user = d.result

            if user:
                if analysis.startswith('user-activity'):
                    import smwactivity
                    if analysis == 'user-activity-all':
                        smwactivity.activityall(cursor=cursor, range='user', entity=user, title='User:%s @ %s' % (user, self.wiki))
                    elif analysis == 'user-activity-yearly':
                        smwactivity.activityyearly(cursor=cursor, range='user', entity=user, title='User:%s @ %s' % (user, self.wiki))
                    elif analysis == 'user-activity-monthly':
                        smwactivity.activitymonthly(cursor=cursor, range='user', entity=user, title='User:%s @ %s' % (user, self.wiki))
                    elif analysis == 'user-activity-dow':
                        smwactivity.activitydow(cursor=cursor, range='user', entity=user, title='User:%s @ %s' % (user, self.wiki))
                    elif analysis == 'user-activity-hourly':
                        smwactivity.activityhourly(cursor=cursor, range='user', entity=user, title='User:%s @ %s' % (user, self.wiki))
                    pylab.show()
        elif analysis.startswith('page'):
            import smwlist
            list = smwlist.listofpages(cursor=cursor)
            d = DialogListbox(root, title="AAA", list=list)
            page = d.result

            if page:
                if analysis.startswith('page-activity'):
                    import smwactivity
                    if analysis == 'page-activity-all':
                        smwactivity.activityall(cursor=cursor, range='page', entity=page, title='Page:%s @ %s' % (page, self.wiki))
                    elif analysis == 'page-activity-yearly':
                        smwactivity.activityyearly(cursor=cursor, range='page', entity=page, title='Page:%s @ %s' % (page, self.wiki))
                    elif analysis == 'page-activity-monthly':
                        smwactivity.activitymonthly(cursor=cursor, range='page', entity=page, title='Page:%s @ %s' % (page, self.wiki))
                    elif analysis == 'page-activity-dow':
                        smwactivity.activitydow(cursor=cursor, range='page', entity=page, title='Page:%s @ %s' % (page, self.wiki))
                    elif analysis == 'page-activity-hourly':
                        smwactivity.activityhourly(cursor=cursor, range='page', entity=page, title='Page:%s @ %s' % (page, self.wiki))
                    pylab.show()
                elif analysis == 'page-edithistorygraph':
                    import smwgraph
                    smwgraph.graphPageHistory(cursor=cursor, range='page', entity=page)
                elif analysis == 'page-geoiplocation':
                    import smwgeolocation
                    smwgeolocation.GeoLocationGraph(cursor=cursor, range='page', entity=page, title=self.wiki)
                    pylab.show()
        elif analysis.startswith('reverts'):
            import smwreverts
            smwreverts.revertsEvolution(cursor=cursor, title='Reverts evolution @ %s' % (self.wiki))
            pylab.show()
        elif analysis.startswith('newpages'):
            import smwnewpages
            smwnewpages.newpagesEvolution(cursor=cursor, title='Newpages evolution @ %s' % (self.wiki))
            pylab.show()
        elif analysis.startswith('newusers'):
            import smwnewusers
            smwnewusers.newusersEvolution(cursor=cursor, title='Newusers evolution @ %s' % (self.wiki))
            pylab.show()
        elif analysis.startswith('graph-user-messages'):
            import smwgraph
            smwgraph.graphUserMessages(cursor=cursor)
        elif analysis.startswith('graph-user-edits-network'):
            import smwgraph
            smwgraph.graphUserEditsNetwork(cursor=cursor)
        
        cursor.close()
        conn.close()

def askclose():
    if tkMessageBox.askokcancel("Quit", "Do you really wish to exit?"):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    root.geometry('505x104+0+0')
    root.title('%s (version %s)' % (NAME, VERSION))
    root.protocol("WM_DELETE_WINDOW", askclose)
    #logo
    imagelogo = PhotoImage(file = 'logo.gif')
    labellogo = Label(root, image=imagelogo)
    labellogo.grid(row=0, column=0, rowspan=3, sticky=W)
    app = App(root)
    root.mainloop()
