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



class Tab:
    def __init__(self, type=TAB_MESSAGE):
        self._type = type 
        # just a holder for now

class mainWindow(gtk.GtkWindow):         # Usual Base
    def __init__(self, title='pygtk app', width=None, height=None):
        gtk.GtkWindow.__init__(self)
        self.set_title(title)
        if width is None:
            if gtk.screen_width() > 300:      ## Fit the display
                width = 320
                height = 200
            else:
                width = 240
                height = 300

        self.tabs = []
        self.cols = {};

        self.roster_selected = None

        self.cmap = self.get_colormap()
        self.cols['blue']  = self.cmap.alloc('blue')
        self.cols['red']   = self.cmap.alloc('red')
        
        self.set_usize(width,height)
        self.connect("delete_event", self.quit)
        
        self.box = gtk.GtkVBox()
        self.add(self.box)
        self.box.show()
        self.init_menu()        

        self.notebook = gtk.GtkNotebook()
        self.notebook.set_tab_pos (gtk.POS_BOTTOM);
        self.notebook.set_scrollable( gtk.TRUE ) 


        self.box.pack_end(self.notebook, fill=gtk.TRUE, expand=gtk.TRUE)

        self.notebook.show()
        self.show()

    def addRosterTab(self,roster):
        print roster
        self.tabs.append(Tab(TAB_ROSTER))
        this_tab = self.tabs[-1]
        this_tab.jid = 'roster'

        this_tab.box = gtk.GtkVBox()
        this_tab.scroll = gtk.GtkScrolledWindow()

        this_tab.clist = gtk.GtkCList(2)
        this_tab.clist.column_titles_show()
        this_tab.clist.set_column_title(0,'Jid')
        this_tab.clist.set_column_title(1,'Status')
        this_tab.clist.set_column_width(0,200);

        this_tab.clist.row_is_visible(gtk.TRUE)
        
        this_tab.clist.connect("select_row" , self.rosterSelectCB)

        this_tab.roster_tree = gtk.GtkCTree( 1, 0 )
        for item in roster:
            this_tab.clist.append( [ str(item['jid']), str(item['status']) ] )

        this_tab.scroll.add(this_tab.clist)
        this_tab.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        this_tab.box.pack_start(this_tab.scroll, fill=gtk.TRUE, expand=gtk.TRUE)

        this_tab.hbox = gtk.GtkHBox()
        #this_tab.entry = gtk.GtkEntry()
        #this_tab.hbox.pack_start(this_tab.entry, fill=gtk.TRUE, expand=gtk.TRUE)
        this_tab.button = gtk.GtkButton('chat')
        this_tab.hbox.pack_start(this_tab.button, fill=gtk.FALSE, expand=gtk.FALSE)
        this_tab.box.pack_end(this_tab.hbox, fill=gtk.TRUE, expand=gtk.FALSE)

        self.notebook.append_page(this_tab.box,gtk.GtkLabel('roster'))
        self.notebook.show_all()

    def rosterSelectCB(self, *args):
        self.roster_selected = int(args[1])
        
    def update_roster_tab(self,roster):
        clist = self.tabs[0].clist
        clist.clear()
        for item in roster:
            clist.append( [ str(item['jid']), str(item['status']) ] )

    def addChatTab(self,jid): ## can pass callback function in
        self.tabs.append(Tab(TAB_MESSAGE))

        this_tab = self.tabs[-1]
        this_tab.jid = jid
        this_tab.box = gtk.GtkVBox()
        this_tab.kill_button = gtk.GtkButton('X')
        this_tab.box.pack_start(this_tab.kill_button, fill=gtk.FALSE, expand=gtk.FALSE)
        this_tab.kill_button.connect('clicked', self.removeTab)
        
        this_tab.scroll = gtk.GtkScrolledWindow()
        this_tab.txt = gtk.GtkText()
        this_tab.txt.set_word_wrap( gtk.TRUE )
        this_tab.scroll.add(this_tab.txt)
        this_tab.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        this_tab.box.pack_start(this_tab.scroll, fill=gtk.TRUE, expand=gtk.TRUE)

        this_tab.hbox = gtk.GtkHBox()
        this_tab.entry = gtk.GtkEntry()
        this_tab.hbox.pack_start(this_tab.entry, fill=gtk.TRUE, expand=gtk.TRUE)
        this_tab.button = gtk.GtkButton('send')
        this_tab.hbox.pack_end(this_tab.button, fill=gtk.FALSE, expand=gtk.FALSE)
        this_tab.box.pack_end(this_tab.hbox, fill=gtk.TRUE, expand=gtk.FALSE)
        
        self.notebook.append_page(this_tab.box,gtk.GtkLabel(jid))
        self.notebook.show_all()
        
        this_tab.entry.grab_focus()
        this_tab.event_connected = 0

    def removeTab(self,*args):
        tab_no = self.notebook.get_current_page()
        self.notebook.remove_page(tab_no)
        del(self.tabs[tab_no])

    def addPresenceTab(self,jid,txt):
        self.tabs.append(Tab(TAB_PRESENCE))
        this_tab = self.tabs[-1]
        this_tab.jid = jid

        this_tab.box = gtk.GtkVBox()
        this_tab.label = gtk.GtkLabel(txt)
        this_tab.box.pack_start(this_tab.label, fill=gtk.FALSE, expand=gtk.FALSE)

        this_tab.hbox = gtk.GtkHBox()
        this_tab.no_button = gtk.GtkButton('no')
        this_tab.hbox.pack_start(this_tab.no_button, fill=gtk.FALSE, expand=gtk.TRUE)
        this_tab.no_button.connect('clicked', self.removeTab)
        this_tab.yes_button = gtk.GtkButton('yes')
        this_tab.hbox.pack_end(this_tab.yes_button, fill=gtk.FALSE, expand=gtk.FALSE)
        this_tab.box.pack_end(this_tab.hbox, fill=gtk.TRUE, expand=gtk.FALSE)
        
        self.notebook.append_page(this_tab.box,gtk.GtkLabel(jid))
        self.notebook.show_all()

        return len(self.tabs)-1
        
    def displayMessage(self,jid,body):
        tab_no = self.findTab(jid)
        if tab_no is None: # do we have a window
            self.addChatTab(jid)
            print "DEBUG -> ", len(self.tabs) 
            self.notebook.set_page( len(self.tabs)  )
            tab_no = len(self.tabs)-1

        self.tabs[tab_no].txt.insert(None,self.cols['red'], None, "<%s> " % jid)
        self.tabs[tab_no].txt.insert(None,None, None, "%s\n" % body)
        return tab_no
        
    def findTab(self,jid,type=TAB_MESSAGE):
        i = 0
        for t in self.tabs:
            if t.jid == jid and t._type == type: return i
            i = i + 1
        return None
    
    def init_menu(self):
        pass
    
    def quit(self, *args):
        print "got exit ?"
        gtk.mainquit()


class JabberClient(Jabber.Connection):
    def __init__(self,server,username,password,resource):
        self.mainwin = mainWindow("jabber app")

        Jabber.Connection.__init__(self,host=server)
        try:
            self.connect()
        except XMLStream.error, e:
            print "Couldn't connect: %s" % e 
            sys.exit(0)
        else:
            print "Connected"
            
        if self.auth(username,password,resource):
            print "Logged in as %s to server %s" % ( username, server )
        else:
            print "eek -> ", con.lastErr, con.lastErrCode
            sys.exit(1)

        ## Build the roster Tab ##
        self.roster = []
        r = self.requestRoster()
        for jid in r.keys():
            if r[jid]['subscription'] == 'both':
                status = 'offline'
            else:
                status = 'pending'
            self.roster.append( { 'jid':jid, 'status': status } )
        self.mainwin.addRosterTab(self.roster)
        
        self.sendInitPresence()                                  
        self.JID = username + "@" + server 

        self.mainwin.tabs[0].button.connect('clicked', self.newMessageTab)

    def  updateRoster(self, jid, status):
        if string.find(jid, '/') != -1:
            jid = string.split(jid,'/')[0]
        for item in self.roster:
            if item['jid'] == jid: item['status'] = status
        self.mainwin.update_roster_tab(self.roster)

    def newMessageTab(self, *args):
        if self.mainwin.roster_selected != None:
            jid = self.roster[self.mainwin.roster_selected]['jid']
            self.mainwin.addChatTab(jid)
            self.mainwin.tabs[self.mainwin.findTab(jid)].button.connect('clicked', self.messageSend )
            self.mainwin.tabs[self.mainwin.findTab(jid)].entry.connect('activate', self.messageSend )
            
    def messageSend(self, *args):
        ## find out what tab is focused ##
        tab_no = self.mainwin.notebook.get_current_page()
        ## build the message for the inputted text ##
        msg = Jabber.Message(self.mainwin.tabs[tab_no].jid,
                             self.mainwin.tabs[tab_no].entry.get_text() )
        msg.setType('chat')
        ## send it ##
        self.send(msg)
        ## clear the tabs input field ##
        self.mainwin.tabs[tab_no].entry.set_text('')
        ## show the sent text it the tabs text area ##
        self.mainwin.tabs[tab_no].txt.insert(None,None,None, "<%s> %s\n" % ( self.JID, msg.getBody()) )

    def messageHandler(self, msg_obj):
        jid = msg_obj.getFrom().getBasic();
        body = msg_obj.getBody()
        tab_no = self.mainwin.displayMessage(jid, body)
        if not self.mainwin.tabs[tab_no].event_connected:
            self.mainwin.tabs[tab_no].button.connect('clicked', self.messageSend )
            self.mainwin.tabs[tab_no].entry.connect('activate', self.messageSend )
            self.mainwin.tabs[tab_no].event_connected = 1
        
    def presenceHandler(self, prs):
        who = str(prs.getFrom())
        type = prs.getType()
        if type == None: type = 'available'

        if type == 'available':
            self.updateRoster(who,'online')
        elif type == 'unavailable':
            self.updateRoster(who,'offline')

        if type == 'subscribe':
            tab_no = self.mainwin.addPresenceTab(who,
                   "%s has requested a subscription to your presence.\n\n Do you wish to add them?")
            self.mainwin.tabs[tab_no].yes_button.connect('clicked', self.presenceSubscribe) 


    def process(self,time=0.1):
        while gtk.events_pending(): gtk.mainiteration()
        Jabber.Connection.process(self,time)
    
    def presenceSubscribe(self,*args):
        tab_no = self.mainwin.notebook.get_current_page()
        jid = self.mainwin.tabs[tab_no].jid
        print "DEBUG: sending to " + jid
        p = Jabber.Presence(to=jid, type='subscribed');
        self.send(p)
        print p
        self.send(Jabber.Presence(to=jid, type='subscribe'))
        self.mainwin.removeTab()
    

def main():
    server   = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    s = JabberClient(server,username,password,'default')
    while(1): s.process()
    
if __name__ == "__main__":
    main()


