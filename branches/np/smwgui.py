# -*- coding: utf-8  -*-
# File: menu1.py

import os
import sqlite3

from Tkinter import *
import tkMessageBox
import tkSimpleDialog

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
        preprocessingmenu.add_command(label="My wiki", command=self.callback)
        preprocessingmenu.add_command(label="Wikimedia", command=self.wikimedia)
        preprocessingmenu.add_command(label="Wikia", command=self.wikia)
        preprocessingmenu.add_separator()
        preprocessingmenu.add_command(label="Exit", command=root.quit)

        #analysis
        analysismenu = Menu(menu)
        menu.add_cascade(label="Analysing", menu=analysismenu)
        analysismenu.add_command(label="Summary", command=self.summary)
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
        import smwqueries
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
        
        if analysis == 'activity-all':
            smwqueries.activity(cursor, '%s @ %s' % (glang, gfamily))
        elif analysis == 'activity-yearly':
            smwqueries.activityyearly(cursor)
        
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
