# -*- coding: utf-8  -*-
# File: menu1.py

import os
import sqlite3

from Tkinter import *
import tkMessageBox
import tkSimpleDialog

# TODO:
# almacenar sesiones o algo parecido para evitar tener que darle a preprocessing para que coja el proyecto, cada vez que arranca el programa
# corregir todas las rutas relativas y hacerlas bien (donde se guardan los dumps, los .dbs, etc)
# capturar parámetros por si se quiere ejecutar sin gui desde consola: smwgui.py --module:summary invalida la gui y muestra los datos por consola

class App:
    def __init__(self, master):
        gfather = ''
        gfamily = ''
        glang = ''
    
        frame = Frame(master, width=300, height=100)
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
        preprocessingmenu.add_command(label="Exit", command=root.quit)

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
        #end global
        
        #begin user-by-user
        userbyusermenu = Menu(analysismenu)
        analysismenu.add_cascade(label="User-by-user", menu=userbyusermenu)
        useractivitymenu = Menu(userbyusermenu)
        userbyusermenu.add_cascade(label="Activity", menu=useractivitymenu)
        useractivitymenu.add_command(label="All", command=lambda: self.analysis('user-activity-all'))
        useractivitymenu.add_separator()
        
        usergraphsmenu = Menu(userbyusermenu)
        userbyusermenu.add_cascade(label="Graphs", menu=usergraphsmenu)
        usergraphsmenu.add_command(label="Edited pages", command=lambda: self.analysis('user-graphs-editedpages'))
        #end user-by-user
        
        #begin page-by-page
        pagebypagemenu = Menu(analysismenu)
        analysismenu.add_cascade(label="Page-by-page", menu=pagebypagemenu)
        
        #end page-by-page
        
        #begin others
        
        
        #end others
        
        #help
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.callback)
    
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
        if analysis == 'global-summary':
            import smwsummary
            smwsummary.summary(cursor=cursor)
        elif analysis == 'global-activity-all':
            import smwactivity
            smwactivity.activityall(cursor=cursor, range='global', title='%s @ %s' % (glang, gfamily))
        elif analysis == 'global-activity-yearly':
            import smwactivity
            smwactivity.activityyearly(cursor=cursor, range='global', title='%s @ %s' % (glang, gfamily))
        elif analysis == 'global-activity-monthly':
            import smwactivity
            smwactivity.activitymonthly(cursor=cursor, range='global', title='%s @ %s' % (glang, gfamily))
        elif analysis == 'global-activity-dow':
            import smwactivity
            smwactivity.activitydow(cursor=cursor, range='global', title='%s @ %s' % (glang, gfamily))
        elif analysis == 'global-activity-hourly':
            import smwactivity
            smwactivity.activityhourly(cursor=cursor, range='global', title='%s @ %s' % (glang, gfamily))
        #user
        elif analysis == 'user-activity-all':
            import smwactivity
            smwactivity.activityall(cursor=cursor, range='user', title='%s @ %s' % (glang, gfamily))
        #elif analysis == 'user-graphs-editedpages':
        #    import smwgraphs
        #    smwgraphs.editedpages(cursor)
        
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
    root.title('StatMediaWiki NP')
    #top = Toplevel() #otra ventana
    status = Label(root, text="...", bd=1, relief=SUNKEN, anchor=W)
    status.pack(side=BOTTOM, fill=X)
    #status.config(text="AA")
    root.protocol("WM_DELETE_WINDOW", askclose)
    app = App(root)
    root.mainloop()
