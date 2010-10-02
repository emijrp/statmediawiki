# -*- coding: utf-8  -*-
# File: menu1.py

import os
import sqlite3

from Tkinter import *
import tkMessageBox
import tkSimpleDialog

# TODO:
# corregir todas las rutas relativas y hacerlas bien (donde se guardan los dumps, los .dbs, etc)
# 

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
        analysismenu.add_command(label="Summary", command=lambda: self.analysis('summary'))
        activitymenu = Menu(analysismenu)
        analysismenu.add_cascade(label="Activity", menu=activitymenu)
        activityyearly = Menu(activitymenu)
        activitymenu.add_command(label="Yearly", command=lambda: self.analysis('activity-yearly'))
        activitymonthly = Menu(activitymenu)
        activitymenu.add_command(label="Monthly", command=lambda: self.analysis('activity-monthly'))
        activitydow = Menu(activitymenu)
        activitymenu.add_command(label="Day of week", command=lambda: self.analysis('activity-dow'))
        activityhourly = Menu(activitymenu)
        activitymenu.add_command(label="Hourly", command=lambda: self.analysis('activity-hourly'))
        activitymenu.add_separator()
        activityall = Menu(activitymenu)
        activitymenu.add_command(label="All", command=lambda: self.analysis('activity-all'))

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
        
        if analysis == 'summary':
            import smwsummary
            smwsummary.summary(cursor)
        elif analysis == 'activity-all':
            import smwactivity
            smwactivity.activityall(cursor, '%s @ %s' % (glang, gfamily))
        elif analysis == 'activity-yearly':
            import smwactivity
            smwactivity.activityyearly(cursor, '%s @ %s' % (glang, gfamily))
        elif analysis == 'activity-monthly':
            import smwactivity
            smwactivity.activitymonthly(cursor, '%s @ %s' % (glang, gfamily))
        elif analysis == 'activity-dow':
            import smwactivity
            smwactivity.activitydow(cursor, '%s @ %s' % (glang, gfamily))
        elif analysis == 'activity-hourly':
            import smwactivity
            smwactivity.activityhourly(cursor, '%s @ %s' % (glang, gfamily))
        
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
    #top = Toplevel() #otra ventana
    status = Label(root, text="...", bd=1, relief=SUNKEN, anchor=W)
    status.pack(side=BOTTOM, fill=X)
    #status.config(text="AA")
    root.protocol("WM_DELETE_WINDOW", askclose)
    app = App(root)
    root.mainloop()
