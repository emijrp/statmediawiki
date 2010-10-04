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
import pylab

# TODO:
# almacenar sesiones o algo parecido para evitar tener que darle a preprocessing para que coja el proyecto, cada vez que arranca el programa
# corregir todas las rutas relativas y hacerlas bien (donde se guardan los dumps, los .dbs, etc)
# capturar parámetros por si se quiere ejecutar sin gui desde consola: smwgui.py --module:summary invalida la gui y muestra los datos por consola
# hacer un listbox para los proyectos de wikimedia y wikia (almacenar en una tabla en un sqlite propia de smw? y actualizar cada poco?) http://download.wikimedia.org/backup-index.html http://community.wikia.com/wiki/Hub:Big_wikis http://community.wikia.com/index.php?title=Special:Newwikis&dir=prev&limit=500&showall=0 http://www.mediawiki.org/wiki/Sites_using_MediaWiki
# Citizendium (interesantes gráficas http://en.citizendium.org/wiki/CZ:Statistics) no publican el historial completo, solo el current http://en.citizendium.org/wiki/CZ:Downloads
# permitir descargar solo el historial de una página (special:Export tiene la pega de que solo muestra las últimas 1000 ediciones), con la Api te traes todo en bloques de 500 pero hay que hacer una función que llame a la API (en vez de utilizar pywikipediabot para no añadir una dependencia más)
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

VERSION = '0.0.3' #StatMediaWiki version
LINUX = platform.system() == 'Linux'

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
        self.homepage = 'http://statmediawiki.forja.rediris.es'
        
        # interface elements
        #description
        self.desc=Label(self.master, text="StatMediaWiki NP (version %s)\nThis program is free software (GPL v3 or later)." % (VERSION), font=("Arial", 7))
        self.desc.grid(row=2, column=1, columnspan=2)
        #quickbuttoms
        self.button1 = Button(self.master, text="Load", command=self.callback, width=12)
        self.button1.grid(row=0, column=1)
        self.button2 = Button(self.master, text="Button #2", command=self.callback, width=12)
        self.button2.grid(row=1, column=1)
        self.button3 = Button(self.master, text="Button #3", command=self.callback, width=12)
        self.button3.grid(row=0, column=2)
        self.button4 = Button(self.master, text="Button #4", command=self.callback, width=12)
        self.button4.grid(row=1, column=2)
        #statusbar
        self.status = Label(self.master, text="Welcome! StatMediaWiki is ready for work", bd=1, justify=LEFT, relief=SUNKEN)
        self.status.grid(row=3, column=0, columnspan=3, sticky=W+E)
        #self.status.config(text="AA")
        
        # create a menu
        menu = Menu(self.master)
        master.config(menu=menu)

        #preprocessing
        preprocessingmenu = Menu(menu)
        menu.add_cascade(label="Preprocessor", menu=preprocessingmenu)
        preprocessingmenu.add_command(label="My wiki", command=self.mywiki)
        preprocessingwikimediamenu = Menu(preprocessingmenu)
        preprocessingmenu.add_cascade(label="Wikimedia", menu=preprocessingwikimediamenu)
        preprocessingwikimediamenu.add_command(label="Full dump", command=self.wikimedia)
        #preprocessingwikimediamenu.add_command(label="Single page", command=self.callback)
        
        preprocessingmenu.add_command(label="Wikia", command=self.wikia)
        preprocessingmenu.add_separator()
        preprocessingmenu.add_command(label="Exit", command=master.quit)

        #analysis
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
        othermenu.add_command(label="very soon...", command=self.callback)
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
        print "Feature doesn't developed"
    
    def mywiki(self):
        import smwparser
        import MySQLdb
        
        mywikiconn = None
        mywikicursor = None
        try:
            host = tkSimpleDialog.askstring("Which host?", "Put a host", initialvalue="localhost")
            user = tkSimpleDialog.askstring("Which database user?", "Put a user", initialvalue="myuser")
            passwd = tkSimpleDialog.askstring("Which database user?", "Put the password for user '%s'" % user, initialvalue="mypass")
            db = tkSimpleDialog.askstring("Which database?", "What is the database name where your wiki is installed?", initialvalue="mydbname")
            mywikiconn = MySQLdb.connect(host=host,user=user, passwd=passwd,db=db)
            mywikicursor = mywikiconn.cursor()
        except:
            print "Hubo un error al conectarse a la base de datos"
        
        path = 'dumps/sqlitedbs'
        filename = 'mywiki.db'
        smwparser.parseMediaWikiMySQLConnect(mywikicursor, path, filename)
        
        mywikicursor.close()
        mywikiconn.close()
    
    def wikimedia(self):
        import smwdownloader
        
        self.status.config(text="Loading list of Wikimedia wikis")
        list = smwdownloader.downloadWikimediaList()
        self.status.config(text="Loaded list of Wikimedia wikis")
        d = DialogListbox(self.master, title='Select a Wikimedia project', list=list)
        if d.result:
            self.site = 'wikimedia'
            self.wiki = d.result
            self.status.config(text="Downloading data for %s" % (self.wiki))
            smwdownloader.downloadWikimediaDump(self.wiki)
            self.status.config(text="Downloaded data for %s OK!" % (self.wiki))
    
    def wikia(self):
        import smwdownloader
        
        self.status.config(text="Loading list of Wikia wikis")
        list = ['answers', 'dc', 'eq2', 'inciclopedia', 'familypedia', 'icehockey', 'lyrics', 'marveldatabase', 'memory-beta', 'memoryalpha', 'psychology', 'recipes', 'swfanon', 'starwars', 'uncyclopedia', 'vintagepatterns', 'wow']
        list.sort()
        self.status.config(text="Loaded list of Wikia wikis")
        d = DialogListbox(self.master, title='Select a Wikia project', list=list)
        if d.result:
            self.site = 'wikia'
            self.wiki = d.result
            self.status.config(text="Downloading data for %s" % (self.wiki))
            smwdownloader.downloadWikiaDump(self.wiki)
            self.status.config(text="Downloaded data for %s OK!" % (self.wiki))
    
    def analysis(self, analysis):
        if not self.site and not self.wiki:
            tkMessageBox.showerror("Error", "You must preprocess first")
            print "Error", "You must preprocess first"
            return
        
        filename = ''
        filedbname = ''
        if self.site == 'wikimedia':
            filename = '%s-latest-pages-meta-history.xml.7z' % (self.wiki)
            filedbname = 'dumps/sqlitedbs/%s.db' % (filename.split('.xml.7z')[0])
        elif self.site == 'wikia':
            filename = '%s-pages_full.xml.gz' % (self.wiki)
            filedbname = 'dumps/sqlitedbs/%s.db' % (filename.split('.xml.gz')[0])
        
        conn = sqlite3.connect(filedbname)
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

    def summary(self):
        print 'summary'
        pass

def askclose():
    if tkMessageBox.askokcancel("Quit", "Do you really wish to exit?"):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    root.geometry('505x104+0+0')
    root.title('StatMediaWiki NP')
    root.protocol("WM_DELETE_WINDOW", askclose)
    #logo
    imagelogo = PhotoImage(file = 'logo.gif')
    labellogo = Label(root, image=imagelogo)
    labellogo.grid(row=0, column=0, rowspan=3, sticky=W)
    app = App(root)
    root.mainloop()
    root.destroy()
