#!/usr/bin/env python2

#
# THIS IS WAY ALPHA CODE. USE AT YOUR OWN RISK ;)
#
#
#
#
#

import gtk
import Jabber
import sys,string

TAB_MESSAGE = 1
TAB_ROSTER  = 2
TAB_PRESENCE = 3
TAB_DEBUG = 4

TRUE = 1
FALSE = 0

class Tab:
    def __init__(self, gui, title):
        self._type = type
        self._notebook = gui.notebook
        self._title = title
        self._id = None
        self._box = gtk.GtkVBox()
        self._main_callback = None
        self._cb = None

        self.cmap = gui.get_colormap()
        self.cols={}
        self.cols['blue']  = self.cmap.alloc('blue')
        self.cols['red']   = self.cmap.alloc('red')
        self.cols['black']   = self.cmap.alloc('black')


    def getID(self): return self._id;
    def setID(self,val): self._id = val;

    def recieve(self,obj): pass
    def setCallBack(self,cb): self._cb = cb
    def getData(self): pass
    def setData(self,val): pass

    def _addToNoteBook(self):
        self._tab_event = gtk.GtkEventBox()
        self._tab_event.connect("clicked", self.tabClicked )
        self._tab_label = gtk.GtkLabel(self._title)
        self._tab_label.show()
        self._tab_event.add(self._tab_label)
        self._notebook.append_page(self._box,self._tab_event)

    def tabClicked(self, *args):
        print "got it"
        return gtk.FALSE

    def highlight(self):
        try:
            l = self.tabs[tab_no].tab_label
        except:
            return

        my_style = l.get_style();
        my_style.fg[gtk.STATE_NORMAL] = self.cols['blue'] 
        l.set_style(my_style)

    def lowlight(self):
        try:
            this_tab = self.tabs[tab_no].tab_label
        except:
            return

        my_style = this_tab.tab_label.get_style();
        my_style.fg[gtk.STATE_NORMAL] = self.cols['black'] 
        this_tab.tab_label.set_style(my_style)

    def removeTab(self,*args):
        tab_no = self.notebook.get_current_page()
        self.notebook.remove_page(tab_no)
        del(self.tabs[tab_no])

        

class Chat_Tab(Tab): ### Make bigger and Better !!!
    def __init__(self, gui, jid):
        Tab.__init__(self, gui, jid.getBasic())

        self._id = str(jid)
        self._kill_button = gtk.GtkButton('X')
        self._box.pack_start(self._kill_button,
                             fill=gtk.FALSE, expand=gtk.FALSE)
        ## this_tab.kill_button.connect('clicked', self.removeTab) ??? ##
        
        self._scroll = gtk.GtkScrolledWindow()
        self._txt = gtk.GtkText()
        self._txt.set_word_wrap( gtk.TRUE )
        self._scroll.add(self._txt)
        self._scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._box.pack_start(self._scroll, fill=gtk.TRUE, expand=gtk.TRUE)

        self._hbox = gtk.GtkHBox()
        self._entry = gtk.GtkEntry()
        self._hbox.pack_start(self._entry, fill=gtk.TRUE, expand=gtk.TRUE)
        self._send_button = gtk.GtkButton('send')
        self._send_button.connect('clicked', self._cb, self)
        self._hbox.pack_end(self._send_button, fill=gtk.FALSE, expand=gtk.FALSE)
        self._box.pack_end(self._hbox, fill=gtk.TRUE, expand=gtk.FALSE)

        self._box.show_all()
        self._addToNoteBook()
        self._entry.grab_focus()

        ## this_tab.event_connected = 0 ??

    def recieve(self,obj):
        if str(obj.__class__) != 'Jabber.Message': return FALSE
        if obj.getFrom().getBasic() == self._title:
            self._txt.insert(None,self.cols['red'], None,
                             "<%s> " % obj.getFrom().getBasic())
            self._txt.insert(None,None, None, "%s\n" % obj.getBody())
            return TRUE
        return FALSE
    
    def getData(self):
        txt = self._entry.get_text() 
        self._entry.set_text('')
        self._txt.insert(None,None,None, "<%s> %s\n" % ( self._id, txt) )
        return txt


class Roster_Tab(Tab): ### Make bigger and Better !!!
    def __init__(self, gui, title, roster):
        Tab.__init__(self, gui, title)
        self._roster_selected = None
        self._rows = []

        self._scroll = gtk.GtkScrolledWindow()

        self._clist = gtk.GtkCList(2)
        self._clist.column_titles_show()
        self._clist.set_column_title(0,'Jid')
        self._clist.set_column_title(1,'Status')
        self._clist.set_column_width(0,200);

        self._clist.row_is_visible(gtk.TRUE)
        
        self._clist.connect("select_row" , self.rosterSelectCB)

        for item in roster:
            self._clist.append( [ str(item['jid']), str(item['status']) ] )
            self._rows.append( { 'jid':str(item['jid']) ,
                                 'status':str(item['status']) } )
            
        self._scroll.add(self._clist)
        self._scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._box.pack_start(self._scroll, fill=gtk.TRUE, expand=gtk.TRUE)

        self._hbox = gtk.GtkHBox()
        self._button = gtk.GtkButton('chat')
        self._hbox.pack_start(self._button, fill=gtk.FALSE, expand=gtk.FALSE)
        self._box.pack_end(self._hbox, fill=gtk.TRUE, expand=gtk.FALSE)

        self._box.show_all()
        self._addToNoteBook()
    
        # just a holder for now
    def rosterSelectCB(self, *args):
        self._roster_selected = int(args[1])

    def get_roster_selection(self):
        return self._rows[self._roster_selected]['jid']

    def recieve(self,obj):
        if str(obj.__class__) != 'Jabber.Presence': return FALSE
        print "recieved presence"
        for row in self._rows:
            print "cjecking ", Jabber.JID(row['jid']).getBasic() ,obj.getFrom().getBasic()
            if Jabber.JID(row['jid']).getBasic() == obj.getFrom().getBasic():
                print "updating"
                type = obj.getType()
                if type == None: type = 'available'

                if type == 'available':
                    row['status'] = 'online'
                elif type == 'unavailable':
                    row['status'] = 'offline'
                self.repaint()
                return TRUE
        return FALSE

    def repaint(self):
        self._clist.clear()
        for row in self._rows:
            self._clist.append( [ str(row['jid']), str(row['status']) ] )

    def update_roster_tab(self,roster):
        clist = self.tabs[0].clist
        clist.clear()
        for item in roster:
            clist.append( [ str(item['jid']), str(item['status']) ] )


class mainWindow(gtk.GtkWindow):         # Usual Base
    def __init__(self, title='pygtk app', roster=None,
                 width=None, height=None):
        gtk.GtkWindow.__init__(self)
        self.set_title(title)
        if width is None:
            if gtk.screen_width() > 300:      ## Fit the display
                width = 320
                height = 200
            else:
                width = 240
                height = 300

        self._tabs = []
        self.cols = {};

        self.roster_selected = None

        
        self.set_usize(width,height)
        self.connect("delete_event", self.quit)
        
        self.box = gtk.GtkVBox()
        self.add(self.box)
        self.box.show()
        #self.init_menu()        

        self.notebook = gtk.GtkNotebook()
        self.notebook.set_tab_pos (gtk.POS_BOTTOM);
        self.notebook.set_scrollable( gtk.TRUE ) 

        self.box.pack_end(self.notebook, fill=gtk.TRUE, expand=gtk.TRUE)

        self._tabs.append( Roster_Tab(self, 'roster', roster) )

        self.notebook.show()
        self.show()

    def getTabs(self):
        return self._tabs

    def getTab(self,val):
        return self._tabs[val]

    def addTab(self,tab_obj):
        self._tabs.append( tab_obj )
        return tab_obj
#    def displayMessage(self,jid,body):
#        tab_no = self.findTab(jid)
#        if tab_no is None: # do we have a window
#            self.addChatTab(jid)
#            print "DEBUG -> ", len(self.tabs) 
#            self.notebook.set_page( len(self.tabs)  )
#            tab_no = len(self.tabs)-1
#
#        self.tabs[tab_no].txt.insert(None,self.cols['red'], None, "<%s> " % jid)
#        self.tabs[tab_no].txt.insert(None,None, None, "%s\n" % body)
#        return tab_no
#        
#    def findTab(self,jid,type=TAB_MESSAGE):
#        i = 0
#        for t in self.tabs:
#            if t.jid == jid and t._type == type: return i
#            i = i + 1
#        return None
#    
#    
    def quit(self, *args):
        print "got exit ?"
        gtk.mainquit()


class JabberClient(Jabber.Connection):
    def __init__(self,server,username,password,resource):
        
        print "connecting"
        Jabber.Connection.__init__(self,host=server,log='Dummy')
        try:
            self.connect()
        except XMLStream.error, e:
            print "Couldn't connect: %s" % e 
            sys.exit(0)
        else:
            print "Connected"
        print "logging in"
        if self.auth(username,password,resource):
            print "Logged in as %s to server %s" % ( username, server )
        else:
            print "eek -> ", con.lastErr, con.lastErrCode
            sys.exit(1)

        print "requesting roster"
        ## Build the roster Tab ##
        self.roster = []
        r = self.requestRoster()
        for jid in r.keys():
            if r[jid]['subscription'] == 'both':
                status = 'offline'
            else:
                status = 'pending'
            self.roster.append( { 'jid':jid, 'status': status } )

        self.gui = mainWindow("jabber app",roster=self.roster)

        ##self.mainwin.addRosterTab(Roster_Tab,self.roster)
        ##self.mainwin.addDebugTab()
        
        self.sendInitPresence()                                  
        ##self.JID = username + "@" + server 
        self.gui.getTab(0)._button.connect('clicked', self.addChatTabViaRoster )
        ##self.mainwin.tabs[0].button.connect('clicked', self.newMessageTab)

    def dispatch_to_gui(self,obj):
        recieved = FALSE
        for t in self.gui.getTabs():
            if t.recieve(obj): recieved = TRUE
        return recieved

##    def  updateRoster(self, jid, status):
##        if string.find(jid, '/') != -1:
##            jid = string.split(jid,'/')[0]
##        for item in self.roster:
##            if item['jid'] == jid: item['status'] = status
##        self.mainwin.update_roster_tab(self.roster)
##
##    def newMessageTab(self, *args):
##        if self.mainwin.roster_selected != None:
##            jid = self.roster[self.mainwin.roster_selected]['jid']
##            self.mainwin.addChatTab(jid)
##            self.mainwin.tabs[self.mainwin.findTab(jid)].button.connect('clicked', self.messageSend )
##            self.mainwin.tabs[self.mainwin.findTab(jid)].entry.connect('activate', self.messageSend )
##            
##    def messageSend(self, *args):
##        print args
##        ## find out what tab is focused ##
##        tab_no = self.mainwin.notebook.get_current_page()
##        ## build the message for the inputted text ##
##        msg = Jabber.Message(self.mainwin.tabs[tab_no].jid,
##                             self.mainwin.tabs[tab_no].entry.get_text() )
##        msg.setType('chat')
##        ## send it ##
##        self.send(msg)
##        ## clear the tabs input field ##
##        self.mainwin.tabs[tab_no].entry.set_text('')
##        ## show the sent text it the tabs text area ##
##        self.mainwin.tabs[tab_no].txt.insert(None,None,None, "<%s> %s\n" % ( self.JID, msg.getBody()) )
##
    def addChatTabViaRoster(self, *args):
        jid_raw = self.gui.getTab(0).get_roster_selection()
        if jid_raw:
            print jid_raw
            jid = Jabber.JID(jid_raw)
            self.gui.addTab( Chat_Tab(self.gui, jid) )
            self.gui.getTab(-1)._send_button.connect('clicked',
                                                     self.messageSend,
                                                     self.gui.getTab(-1) )

    def messageSend(self, *args):
        tab = args[-1]
        msg = tab.getData()
        msg_obj = Jabber.Message(tab._id, msg)
        msg_obj.setType('chat')
        self.send(msg_obj)


    def messageHandler(self, msg_obj):
        print msg_obj
        if not self.dispatch_to_gui(msg_obj):
            self.gui.addTab(
                Chat_Tab(self.gui, msg_obj.getFrom())
                ).recieve(msg_obj)
            self.gui._tabs[-1]._send_button.connect('clicked',
                                                    self.messageSend,
                                                    self.gui._tabs[-1] )

                
    def presenceHandler(self, prs_obj):
        print "got presence 1"
        self.dispatch_to_gui(prs_obj)

    
    def process(self,time=0.1):
        while gtk.events_pending(): gtk.mainiteration()
        Jabber.Connection.process(self,time)
    

def main():
    server   = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    s = JabberClient(server,username,password,'default')
    while(1): s.process()
    
if __name__ == "__main__":
    main()  

















