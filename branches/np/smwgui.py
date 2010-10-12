# -*- coding: utf-8  -*-
# File: menu1.py

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

# TODO:
# almacenar sesiones o algo parecido para evitar tener que darle a preprocessing para que coja el proyecto, cada vez que arranca el programa
# corregir todas las rutas relativas y hacerlas bien (donde se guardan los dumps, los .dbs, etc)
# capturar parámetros por si se quiere ejecutar sin gui desde consola: smwgui.py --module:summary invalida la gui y muestra los datos por consola
# hacer un listbox para los proyectos de wikimedia y wikia (almacenar en una tabla en un sqlite propia de smw? y actualizar cada poco?) http://download.wikimedia.org/backup-index.html http://community.wikia.com/wiki/Hub:Big_wikis http://community.wikia.com/index.php?title=Special:Newwikis&dir=prev&limit=500&showall=0 http://www.mediawiki.org/wiki/Sites_using_MediaWiki
# Citizendium (interesantes gráficas http://en.citizendium.org/wiki/CZ:Statistics) no publican el historial completo, solo el current http://en.citizendium.org/wiki/CZ:Downloads
# permitir descargar solo el historial de una página (special:Export tiene la pega de que solo muestra las últimas 1000 ediciones), con la Api te traes todo en bloques de 500 pero hay que hacer una función que llame a la API (en vez de utilizar pywikipediabot para no añadir una dependencia más)
# permitir descargar todos los dumps en lote, y luego preprocesarlos
# hay otros dumps a parte de los 7z que tienen información útil, por ejemplo los images.sql con metadatos de las fotos, aunque solo los publica wikipedia
# usar getopt para capturar parámetros desde consola
# i18n http://www.learningpython.com/2006/12/03/translating-your-pythonpygtk-application/
# documentation

# Ideas para análisis de wikis:
# * reverts rate: ratio de reversiones (como de eficiente es la comunidad)
# * ip geolocation: http://software77.net/geo-ip/?license
#
# Ideas para otros análisis que no usan dumps pero relacionados con wikis o wikipedia:
# * el feed de donaciones
# log de visitas de domas?
# conectarse a irc y poder hacer estadisticas en vivo?
#
# embeber mejor las gráficas en Tk? http://matplotlib.sourceforge.net/examples/user_interfaces/embedding_in_tk.py así cuando se cierra SMW, se cerrarán las gráficas; sería hacer una clase como listbox, a la que se le pasa la figura f (las funciones que generan las gráficas deberían devolver la f, ahora no devuelven nada)

NAME = 'StatMediaWiki NP'
VERSION = '0.0.5' #StatMediaWiki version
LINUX = platform.system() == 'Linux'
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
        self.homepage = 'http://statmediawiki.forja.rediris.es'

        # interface elements
        #description
        self.desc=Label(self.master, text="%s (version %s)\nThis program is free software (GPL v3 or higher)." % (NAME, VERSION), font=("Arial", 7))
        self.desc.grid(row=2, column=1, columnspan=2)
        #quick buttons
        self.button1 = Button(self.master, text="Load", command=self.loadDBFilename, width=12)
        self.button1.grid(row=0, column=1)
        self.button2 = Button(self.master, text="Button #2", command=self.callback, width=12)
        self.button2.grid(row=1, column=1)
        self.button3 = Button(self.master, text="Button #3", command=self.callback, width=12)
        self.button3.grid(row=0, column=2)
        self.button4 = Button(self.master, text="Button #4", command=self.callback, width=12)
        self.button4.grid(row=1, column=2)
        #statusbar
        self.status = Label(self.master, text="Welcome! %s is ready for work" % (NAME), bd=1, justify=LEFT, relief=SUNKEN)
        self.status.grid(row=3, column=0, columnspan=3, sticky=W+E)
        #self.status.config(text="AA")

        # create a menu
        menu = Menu(self.master)
        master.config(menu=menu)

        #begin downloader
        downloadermenu = Menu(menu)
        menu.add_cascade(label="Downloader", menu=downloadermenu)
        downloadermywikimenu = Menu(downloadermenu)
        downloadermenu.add_cascade(label="My wiki", menu=downloadermywikimenu)
        downloadermywikimenu.add_command(label="Database connection", command=self.callback)
        downloadermywikimenu.add_command(label="XML Dump", command=self.callback)
        #downloaderwikimediamenu = Menu(downloadermenu)
        #downloadermenu.add_cascade(label="Wikimedia", menu=downloaderwikimediamenu)
        downloadermenu.add_command(label="Wikimedia", command=lambda: self.downloader('wikimedia'))
        downloadermenu.add_command(label="Wikia", command=lambda: self.downloader('wikia'))
        downloadermenu.add_command(label="Citizendium", command=lambda: self.downloader('citizendium'))
        #end downloader

        #begin preprocessor
        preprocessormenu = Menu(menu)
        menu.add_cascade(label="Preprocessor", menu=preprocessormenu)
        preprocessormenu.add_command(label="My wiki", command=self.mywiki)
        preprocessorwikimediamenu = Menu(preprocessormenu)
        preprocessormenu.add_cascade(label="Wikimedia", menu=preprocessorwikimediamenu)
        preprocessorwikimediamenu.add_command(label="XML Dump", command=lambda: self.parser('wikimedia'))
        preprocessorwikimediamenu.add_command(label="IRC feed", command=self.callback)
        preprocessorwikimediamenu.add_command(label="Single page", command=self.callback)
        preprocessormenu.add_command(label="Wikia", command=lambda: self.parser('wikia'))
        preprocessormenu.add_command(label="Citizendium", command=lambda: self.parser('citizendium'))
        #preprocessormenu.add_separator()
        #preprocessormenu.add_command(label="Exit", command=master.quit)
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
        globalactivitymenu.add_command(label="Day of week", command=lambda: self.analysis('global-activity-dow'))
        globalactivitymenu.add_command(label="Hourly", command=lambda: self.analysis('global-activity-hourly'))
        #end activity
        globalmenu.add_command(label="GeoIP location", command=lambda: self.analysis('global-geoiplocation'))
        globalmenu.add_command(label="Pareto", command=lambda: self.analysis('global-pareto'))
        #globalmenu.add_command(label="Graph", command=lambda: self.analysis('global-graph'))
        #end global

        #end analyser

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
        helpmenu.add_command(label="StatMediaWiki homepage", command=lambda: webbrowser.open_new_tab(homepage))

    def callback(self):
        self.setStatus("Feature doesn't developed yet. Coming soon.")

    def setStatus(self, text):
        self.status.config(text=text)
        print text

    def loadDBFilename(self):
        initialdir = 'dumps/sqlitedbs'
        if PATH:
            initialdir = '%s/%s' % (PATH, initialdir)
        self.dbfilename = tkFileDialog.askopenfilename(initialdir=initialdir)
        self.setStatus("Loaded %s" % (self.dbfilename.split('/')[-1]))

    def mywiki(self):
        import smwparser
        import MySQLdb

        mywikiconn = None
        mywikicursor = None

        host = tkSimpleDialog.askstring("Which host?", "Put a host", initialvalue="localhost")
        user = tkSimpleDialog.askstring("Which database user?", "Put a user", initialvalue="myuser")
        passwd = tkSimpleDialog.askstring("Which database user?", "Put the password for user '%s'" % user, initialvalue="mypass")
        db = tkSimpleDialog.askstring("Which database?", "What is the database name where your wiki is installed?", initialvalue="mydbname")
        mywikiconn = MySQLdb.connect(host=host,user=user, passwd=passwd,db=db)
        mywikicursor = mywikiconn.cursor()

        path = 'dumps/sqlitedbs'
        filename = 'mywiki.db'
        smwparser.parseMediaWikiMySQLConnect(mywikicursor, path, filename)

        mywikicursor.close()
        mywikiconn.close()

    def downloader(self, site):
        import smwdownloader

        self.site = site
        self.wiki = ''
        initialdir = 'dumps'
        dumpfilename = ''
        if self.site == 'wikimedia':
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
        elif self.site == 'citizendium':
            self.wiki = 'cz'
            #http://locke.citizendium.org/download/cz.dump.current.xml.gz
            #todo también tiene uno en bz2 http://locke.citizendium.org/download/cz.dump.current.xml.bz2
            dumpfilename = '%s.dump.current.xml.gz' % (self.wiki)
            dumpfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir, initialfile=dumpfilename, defaultextension='.xml.gz')

        if self.wiki and dumpfilename:
            self.setStatus("Downloading data for %s @ %s" % (self.wiki, self.site))
            if self.site == 'wikimedia':
                smwdownloader.downloadWikimediaDump(self.wiki, dumpfilename)
            elif self.site == 'wikia':
                smwdownloader.downloadWikiaDump(self.wiki, dumpfilename)
            elif self.site == 'citizendium':
                smwdownloader.downloadCitizendiumDump(self.wiki, dumpfilename)
            self.setStatus("Downloaded data for %s @ %s OK!" % (self.wiki, self.site))

    def parser(self, site):
        import smwparser

        self.site = site
        initialdir = 'dumps'
        initialdir2 = 'dumps/sqlitedbs'
        dumpfilename = ''
        self.dbfilename = ''
        if self.site == 'wikimedia':
            dumpfilename = tkFileDialog.askopenfilename(initialdir=initialdir, initialfile='', filetypes=[('7zip', '*.7z')])
            initialfile = '%s.db' % (dumpfilename.split('/')[-1].split('.xml.7z')[0])
            self.dbfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir2, initialfile=initialfile, filetypes=[('SQLite3', '*.db')])
        elif self.site == 'wikia':
            dumpfilename = tkFileDialog.askopenfilename(initialdir=initialdir, initialfile='', filetypes=[('Gzip', '*.gz')])
            initialfile = '%s.db' % (dumpfilename.split('/')[-1].split('.xml.gz')[0])
            self.dbfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir2, initialfile=initialfile, filetypes=[('SQLite3', '*.db')])
        elif self.site == 'citizendium':
            dumpfilename = tkFileDialog.askopenfilename(initialdir=initialdir, initialfile='', filetypes=[('Gzip', '*.gz')])
            initialfile = '%s.db' % (dumpfilename.split('/')[-1].split('.xml.gz')[0])
            self.dbfilename = tkFileDialog.asksaveasfilename(initialdir=initialdir2, initialfile=initialfile, filetypes=[('SQLite3', '*.db')])

        if dumpfilename and self.dbfilename:
            dumpfilename2 = dumpfilename.split('/')[-1]
            self.setStatus("Parsing %s @ %s" % (dumpfilename2, self.site))
            if self.site == 'wikimedia':
                smwparser.parseMediaWikiXMLDump(dumpfilename=dumpfilename, dbfilename=self.dbfilename)
            elif self.site == 'wikia':
                smwparser.parseMediaWikiXMLDump(dumpfilename=dumpfilename, dbfilename=self.dbfilename)
            elif self.site == 'citizendium':
                smwparser.parseMediaWikiXMLDump(dumpfilename=dumpfilename, dbfilename=self.dbfilename)
            #tkMessageBox.showinfo("OK", "Parsing complete")
            self.setStatus("Parsed %s @ %s OK!" % (dumpfilename2, self.site))
        else:
            self.setStatus("ERROR: NO DUMP FILENAME OR NO DB FILENAME")

    def analysis(self, analysis):
        if not self.dbfilename:
            message = "You must load a preprocessed dump"
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
            elif analysis == 'global-graph':
                import smwgraph
                smwgraph.graph(cursor=cursor)
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
            elif analysis == 'user-graph':
                import smwgraph
                smwgraph.graphUserEdits(cursor=cursor, range='user', entity=user)
        #elif analysis == 'user-graphs-editedpages':
        #    import smwgraphs
        #    smwgraphs.editedpages(cursor)
        #page
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
                    smwgraph.graph(cursor=cursor, range='page', entity=page)
                elif analysis == 'page-geoiplocation':
                    import smwgeolocation
                    smwgeolocation.GeoLocationGraph(cursor=cursor, range='page', entity=page, title=self.wiki)
                    pylab.show()

        cursor.close()
        conn.close()

def askclose():
    if tkMessageBox.askokcancel("Quit", "Do you really wish to exit?"):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    root.geometry('505x104+0+0')
    root.title(NAME)
    root.protocol("WM_DELETE_WINDOW", askclose)
    #logo
    imagelogo = PhotoImage(file = 'logo.gif')
    labellogo = Label(root, image=imagelogo)
    labellogo.grid(row=0, column=0, rowspan=3, sticky=W)
    app = App(root)
    root.mainloop()
