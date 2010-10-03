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
# hacer un listbox para los proyectos de wikimedia y wikia (almacenar en una tabla en un sqlite propia de smw? y actualizar cada poco?)

LINUX = platform.system() == 'Linux'

class App:
    def __init__(self, master):
        gfather = ''
        gfamily = ''
        glang = ''
        
        homepage = 'http://statmediawiki.forja.rediris.es'
        
        frame = Frame(master)
        frame.pack()
        # create a menu
        menu = Menu(frame)
        master.config(menu=menu)

        #preprocessing
        preprocessingmenu = Menu(menu)
        menu.add_cascade(label="Preprocessing", menu=preprocessingmenu)
        preprocessingmenu.add_command(label="My wiki", command=self.mywiki)
        preprocessingmenu.add_command(label="Wikimedia", command=self.wikimedia)
        preprocessingmenu.add_command(label="Wikia", command=self.wikia)
        preprocessingmenu.add_separator()
        preprocessingmenu.add_command(label="Exit", command=master.quit)

        #analysis
        analysismenu = Menu(menu)
        menu.add_cascade(label="Analysing", menu=analysismenu)
        
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
        
        usergraphsmenu = Menu(userbyusermenu)
        userbyusermenu.add_cascade(label="Graphs", menu=usergraphsmenu)
        usergraphsmenu.add_command(label="Edited pages", command=lambda: self.analysis('user-graph'))
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
        
        #end page-by-page
        
        #begin others
        
        
        #end others
        
        #help
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About", command=self.callback)
        helpmenu.add_command(label="Help index", command=self.callback)
        helpmenu.add_command(label="StatMediaWiki homepage", command=lambda: webbrowser.open_new_tab(homepage))
    
    def callback(self):
        print "called the callback!"
    
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
        smwparser.parseMyWikiMySQL(mywikicursor, path, filename)
        
        mywikicursor.close()
        mywikiconn.close()
    
    def wikimedia(self):
        global gfather
        global gfamily
        global glang
        
        import smwdownloader
        
        project = tkSimpleDialog.askstring("Which project?", "Put an URL like below", initialvalue="kw.wikipedia.org")
        t = project.split('.')
        if len(t) == 3:
            if t[1] in ['wikipedia', 'wiktionary']:
                gfather = 'wikimedia'
                gfamily = t[1]
                glang = t[0]
                smwdownloader.download(gfather, gfamily, glang)
    
    def wikia(self):
        global gfather
        global gfamily
        global glang
        
        import smwdownloader
        
        project = tkSimpleDialog.askstring("Which project?", "Put an URL like below", initialvalue="inciclopedia.wikia.com")
        t = project.split('.')
        if len(t) == 3:
            if t[1] in ['wikia']:
                gfather = 'wikia'
                gfamily = t[1]
                glang = t[0]
                smwdownloader.download(gfather, gfamily, glang)
    
    def analysis(self, analysis):
        global gfather
        global glang
        global gfamily
        
        filename = ''
        filedbname = ''
        if gfather == 'wikimedia':
            filename = '%swiki-latest-pages-meta-history.xml.7z' % (glang)
            filedbname = 'dumps/sqlitedbs/%s.db' % (filename.split('.xml.7z')[0])
        elif gfather == 'wikia':
            filename = '%s-pages_full.xml.gz' % (glang)
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
                    smwactivity.activityall(cursor=cursor, range='global', title='%s.%s' % (glang, gfamily))
                elif analysis == 'global-activity-yearly':
                    smwactivity.activityyearly(cursor=cursor, range='global', title='%s.%s' % (glang, gfamily))
                elif analysis == 'global-activity-monthly':
                    smwactivity.activitymonthly(cursor=cursor, range='global', title='%s.%s' % (glang, gfamily))
                elif analysis == 'global-activity-dow':
                    smwactivity.activitydow(cursor=cursor, range='global', title='%s.%s' % (glang, gfamily))
                elif analysis == 'global-activity-hourly':
                    smwactivity.activityhourly(cursor=cursor, range='global', title='%s.%s' % (glang, gfamily))
                pylab.show()
            elif analysis == 'global-pareto':
                import smwpareto
                smwpareto.pareto(cursor=cursor, title='%s.%s' % (glang, gfamily))
            elif analysis == 'global-graph':
                import smwgraph
                smwgraph.graph(cursor=cursor)
        #user
        elif analysis.startswith('user'):
            import smwlist
            askframe = Tk()
            askframe.title('Select a user')
            askframe.geometry('300x500')
            scrollbar = Scrollbar(askframe)
            scrollbar.pack(side=RIGHT, fill=Y)
            listbox = Listbox(askframe, width=300, height=30)
            listbox.pack()
            list = smwlist.listofusersandedits(cursor=cursor)
            for user, edits in list:
                i = '%s (%s edits)' % (user, edits)
                listbox.insert(END, i)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            if analysis.startswith('user-activity'):
                import smwactivity
                if analysis == 'user-activity-all':
                    Button(askframe, text="OK", command=lambda: smwactivity.activityall(cursor=cursor, range='user', entity=list[int(listbox.curselection()[0])][0], title='User:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'user-activity-yearly':
                    Button(askframe, text="OK", command=lambda: smwactivity.activityyearly(cursor=cursor, range='user', entity=list[int(listbox.curselection()[0])][0], title='User:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'user-activity-monthly':
                    Button(askframe, text="OK", command=lambda: smwactivity.activitymonthly(cursor=cursor, range='user', entity=list[int(listbox.curselection()[0])][0], title='User:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'user-activity-dow':
                    Button(askframe, text="OK", command=lambda: smwactivity.activitydow(cursor=cursor, range='user', entity=list[int(listbox.curselection()[0])][0], title='User:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'user-activity-hourly':
                    Button(askframe, text="OK", command=lambda: smwactivity.activityhourly(cursor=cursor, range='user', entity=list[int(listbox.curselection()[0])][0], title='User:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                pylab.show()
            elif analysis == 'user-graph':
                import smwgraph
                Button(askframe, text="OK", command=lambda: smwgraph.graphUserEdits(cursor=cursor, range='user', entity=list[int(listbox.curselection()[0])][0])).pack()
            askframe.mainloop()
        #elif analysis == 'user-graphs-editedpages':
        #    import smwgraphs
        #    smwgraphs.editedpages(cursor)
        #page
        elif analysis.startswith('page'):
            import smwlist
            askframe = Tk()
            askframe.title('Select a page')
            askframe.geometry('300x500')
            scrollbar = Scrollbar(askframe)
            scrollbar.pack(side=RIGHT, fill=Y)
            listbox = Listbox(askframe, width=300, height=30)
            listbox.pack()
            list = smwlist.listofpagesandedits(cursor=cursor)
            for title, edits in list:
                i = '%s (%s edits)' % (title, edits)
                listbox.insert(END, i)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            if analysis.startswith('page-activity'):
                import smwactivity
                if analysis == 'page-activity-all':
                    Button(askframe, text="OK", command=lambda: smwactivity.activityall(cursor=cursor, range='page', entity=list[int(listbox.curselection()[0])][0], title='Page:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'page-activity-yearly':
                    Button(askframe, text="OK", command=lambda: smwactivity.activityyearly(cursor=cursor, range='page', entity=list[int(listbox.curselection()[0])][0], title='Page:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'page-activity-monthly':
                    Button(askframe, text="OK", command=lambda: smwactivity.activitymonthly(cursor=cursor, range='page', entity=list[int(listbox.curselection()[0])][0], title='Page:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'page-activity-dow':
                    Button(askframe, text="OK", command=lambda: smwactivity.activitydow(cursor=cursor, range='page', entity=list[int(listbox.curselection()[0])][0], title='Page:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                elif analysis == 'page-activity-hourly':
                    Button(askframe, text="OK", command=lambda: smwactivity.activityhourly(cursor=cursor, range='page', entity=list[int(listbox.curselection()[0])][0], title='Page:%s @ %s.%s' % (list[int(listbox.curselection()[0])][0], glang, gfamily))).pack()
                pylab.show()
            elif analysis == 'page-edithistorygraph':
                import smwgraph
                Button(askframe, text="OK", command=lambda: smwgraph.graph(cursor=cursor, range='page', entity=list[int(listbox.curselection()[0])][0])).pack()
            askframe.mainloop()
        
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
    root.geometry('300x130+0+0')
    root.title('StatMediaWiki NP')
    #logo
    canvas = Canvas(width = 254, height = 82)
    canvas.pack(expand = YES, fill = BOTH)
    logo = PhotoImage(file = 'logo.gif')
    canvas.create_image(0, 0, image = logo, anchor = NW)
    #description
    desc=Label(root, text="StatMediaWiki NP (version 0.0.1)\n(c) 2010 - Present\nThis program is free software (GPL v3 or later)", justify=LEFT)
    desc.pack(side=TOP, anchor=W)
    #top = Toplevel() #otra ventana
    status = Label(root, text="...", bd=1, relief=SUNKEN, anchor=W)
    status.pack(side=BOTTOM, fill=X)
    #status.config(text="AA")
    root.protocol("WM_DELETE_WINDOW", askclose)
    app = App(root)
    root.mainloop()
