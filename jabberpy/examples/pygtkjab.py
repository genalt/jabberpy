#!/usr/bin/env python2

#
# THIS IS WAY ALPHA CODE. USE AT YOUR OWN RISK ;)
#
#
#
#
#

import gtk, GDK
import jabber
import sys,string,os

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

        self.blue_tab_style = gtk.GtkLabel().get_style()
        #self.blue_tab_style.fg[0] = self.cols['blue'] 
        self.red_tab_style = gtk.GtkLabel().get_style()
        #self.red_tab_style.fg[0] = self.cols['red'] 
        #self.default_tab_style = gtk.GtkLabel().get_style()


        self.gui = gui
        
    def getID(self): return self._id;
    def setID(self,val): self._id = val;

    def recieve(self,obj): pass
    def setCallBack(self,cb): self._cb = cb
    def getCallBack(self): return self._cb 
    def getData(self): pass
    def setData(self,val): pass

    def _addToNoteBook(self):
##        self._tab_event = gtk.GtkEventBox()
##        self._tab_event.connect("clicked", self.tabClicked )
        self._tab_label = gtk.GtkLabel(self._title)
        self._tab_label.show()
##        self._tab_event.add(self._tab_label)
#        my_style = self._tab_label.get_style();
#        my_style.fg[gtk.STATE_NORMAL] = self.cols['blue'] 
#        self._tab_label.set_style(my_style)
#
        self._notebook.append_page(self._box,self._tab_label)

    def tabClicked(self, *args):
        print "got it"
        return gtk.FALSE

    def highlight(self):
        style = self._tab_label.get_style()
        self.blue_tab_style = style.copy()
        self.blue_tab_style.fg[0] = self.cols['blue'] 
        #self._tab_label.set_name( "tab2" )
        print "HIGHLIGHTING"
        print "highlighting", str(self.__class__)
#        my_style = self._tab_label.get_style();
#        my_style.bg[gtk.STATE_NORMAL] = self.cols['red'] 
#        for x in range(0,5):
#            print x
#            my_style.bg[x] = self.cols['blue']
        self._tab_label.set_style(self.blue_tab_style)
        #self._tab_label.show()

    def lowlight(self):
        print "LOWLIGHTING"
        style = gtk.GtkLabel().get_style()
        self.red_tab_style = style.copy()
        self.red_tab_style.fg[0] = self.cols['black'] 
        self._tab_label.set_style(style)
        #self._tab_label.set_property("name", "tab1" )
#        label = self._notebook.get_tab_label (self._notebook.get_current_page())
#
#        my_style = label.get_style();
#        my_style.bg[gtk.STATE_NORMAL] = self.cols['blue'] 
#        label.set_style(my_style)
#        #self._tab_label.show()

    def getJID(self):
        return None

    def destroy(self,*args):
        i = 0
        for tab in self.gui._tabs:
            if tab == self:
                self._notebook.remove_page(i)
                del(self.gui._tabs[i])
                ## self.__destroy__ ? 
            i=i+1


class Chat_Tab(Tab): ### Make bigger and Better !!!
    def __init__(self, gui, jid):
        Tab.__init__(self, gui, jid.getStripped())

        self._id = str(jid.getStripped())
        self._kill_button = gtk.GtkButton('X')
        self._box.pack_start(self._kill_button,
                             fill=gtk.FALSE, expand=gtk.FALSE)
        self._kill_button.connect('clicked', self.destroy)
        
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
        #self._send_button.connect('clicked', self._cb, self)
        #self._entry.connect('activate', self._cb, self )
        self._hbox.pack_end(self._send_button, fill=gtk.FALSE, expand=gtk.FALSE)
        self._box.pack_end(self._hbox, fill=gtk.TRUE, expand=gtk.FALSE)

        self._box.show_all()
        self._addToNoteBook()
        self._entry.grab_focus()

        ## this_tab.event_connected = 0 ??

    def getJID(self):
        return self._id


    def recieve(self,obj):
        if str(obj.__class__) != 'jabber.Message': return FALSE
        if obj.getFrom().getStripped() == self._title:
            self._txt.insert(None,self.cols['red'], None,
                             "<%s> " % obj.getFrom().getStripped())
            self._txt.insert(None,None, None, "%s\n" % obj.getBody())
            return TRUE
        return FALSE
    
    def getData(self):
        txt = self._entry.get_text() 
        self._entry.set_text('')
        self._txt.insert(None,None,None, "<%s> %s\n" % ( self._id, txt) )
        return txt


class Roster_Tab(Tab): ### Make bigger and Better !!!
    def __init__(self, gui, title):
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


        _roster = self.gui.jabberObj.getRoster()
        for jid in _roster.getJIDs():
            self._clist.append( [ str(jid), _roster.getOnline(jid) ] )
            
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
        if args[3].type == GDK._2BUTTON_PRESS:
            self._cb()

    def get_roster_selection(self):
        return str(self.gui.jabberObj.getRoster().getJIDs()[self._roster_selected])
        #return self._rows[self._roster_selected]['jid']

    def recieve(self,obj):
        if str(obj.__class__) != 'jabber.Presence': return FALSE
        ## TODO: should recieve iq's too
        self.repaint()
        print "recieved presence"

    def repaint(self):
        self._clist.clear()
        _roster = self.gui.jabberObj.getRoster()
        for jid in _roster.getJIDs():
            self._clist.append( [ str(jid), _roster.getOnline(jid) ] )
            
    def update_roster_tab(self,roster):
        clist = self.tabs[0].clist
        clist.clear()
        for item in roster:
            clist.append( [ str(item['jid']), str(item['status']) ] )


class Logon_dialog(gtk.GtkWindow):                  
                                                 
    def __init__(self, master):

        gtk.GtkWindow.__init__(self)

        self.password = ''
        self.username = ''
        self.server   = 'jabber.org'
        self.done     = None



        self.connect("delete_event", self.delete_event)
        self.master = master

        self.vbox = gtk.GtkVBox(gtk.FALSE,5)
        self.add(self.vbox)

        self.frame_s = gtk.GtkFrame("Server to use")
        self.table_s = gtk.GtkTable(1,6,gtk.FALSE)
        self.server_lbl = gtk.GtkLabel('Server')
        self.server_lbl.set_alignment(1,0.5)
        self.server_entry   = gtk.GtkEntry()

        self.table_s.attach( self.server_lbl,
                             0,2,0,1,xpadding=3,ypadding=2)
        self.table_s.attach( self.server_entry,
                             2,6,0,1,xpadding=3,ypadding=2)
        self.frame_s.add(self.table_s)
        self.vbox.pack_start(self.frame_s)
        
        self.frame = gtk.GtkFrame("Have Account?")
        self.table = gtk.GtkTable(6,6,gtk.FALSE)
        self.username_lbl = gtk.GtkLabel('Username')
        self.username_lbl.set_alignment(1,0.5)
        self.password_lbl = gtk.GtkLabel('Password')
        self.password_lbl.set_alignment(1,0.5)


        self.username_entry = gtk.GtkEntry()

        self.password_entry = gtk.GtkEntry()
        self.password_entry.set_visibility(gtk.FALSE)


        self.table.attach( self.username_lbl,   0,2,1,2,xpadding=3,ypadding=2)
        self.table.attach( self.password_lbl,   0,2,2,3,xpadding=3,ypadding=2) 

        self.table.attach( self.username_entry, 2,6,1,2,xpadding=3,ypadding=2)
        self.table.attach( self.password_entry, 2,6,2,3,xpadding=3,ypadding=2)

        self.save_check = gtk.GtkCheckButton('Save Details')
        self.table.attach( self.save_check, 3,6,4,5,xpadding=3,ypadding=2)

        self.login_button = gtk.GtkButton('Login')
        self.login_button.connect('clicked', self.login)
        self.table.attach( self.login_button, 3,6,5,6,xpadding=5) 
        self.frame.add(self.table)
        
        self.vbox.pack_start(self.frame)
        
        self.frame_acc = gtk.GtkFrame("New User?")
        self.table_acc = gtk.GtkTable(1,1,gtk.FALSE)
        self.button_acc = gtk.GtkButton("Get an Account")
        self.table_acc.attach( self.button_acc, 0,1,0,1,xpadding=5,ypadding=5)
        
        self.frame_acc.add(self.table_acc)
        self.vbox.pack_end(self.frame_acc)

        self.readRC()
        self.username_entry.set_text(self.username)
        self.password_entry.set_text(self.password)
        self.server_entry.set_text(self.server)
        
        self.vbox.show_all()
        self.show()
        self.set_modal(gtk.TRUE)

    def login(self,*args):
        self.password = self.password_entry.get_text()
        self.username = self.username_entry.get_text()
        self.server   = self.server_entry.get_text()
        self.done = gtk.TRUE
        if self.save_check.get_active(): 
            try:
                rcfile = open(os.environ['HOME'] + "/.pyjab",'w')
            except:
                return
            rcfile.write("%s\0%s\0%s\n" % (self.server, self.username, self.password))
            rcfile.close()
        else:
            try: os.remove(os.environ['HOME'] + "/.pyjab")
            except: pass # file dont exist, or I cant delete
            
    def readRC(self):
        try:
            rcfile = open(os.environ['HOME'] + "/.pyjab",'r')
        except:
            return
        self.save_check.set_active(gtk.TRUE)
        data = rcfile.readline()
        self.server, self.username, self.password = data.split("\0")
        rcfile.close()
        return

    def new_account(self,*args):
        self.done = gtk.TRUE

    def delete_event(win, event=None):
        self.hide()
        return gtk.TRUE

    def close(self,*args):
        self.hide()
        del self

class Add_dialog(gtk.GtkDialog):                  
                                                 
    def __init__(self, master):

        gtk.GtkDialog.__init__(self)

        self.jid_str  = None
        self.done     = None

        self.connect("delete_event", self.delete_event)
        self.master = master
        self.set_usize(200,150)

        self.table = gtk.GtkTable(5,2,gtk.FALSE)
        self.jid_lbl = gtk.GtkLabel('JID')

        self.jid_entry   = gtk.GtkEntry()

        self.table.attach( self.jid_lbl,     0,1,0,1)
        self.table.attach( self.jid_entry,   1,2,0,1)

        self.add_button = gtk.GtkButton('Add')
        self.add_button.connect('clicked', self.add)
        self.action_area.pack_start(self.add_button,expand=gtk.FALSE)
        
        self.vbox.pack_start(self.table)
             
        self.vbox.show_all()
        self.action_area.show_all()
        self.show()
        self.set_modal(gtk.TRUE)

    def add(self,*args):
        self.jid = self.jid_entry.get_text()
        self.done = gtk.TRUE

    def delete_event(win, event=None):
        ## self.hide()
        return gtk.FALSE

    def close(self,*args):
        self.hide()
        del self

class Msg_dialog(gtk.GtkDialog):                  
                                                 
    def __init__(self, master):
        gtk.GtkDialog.__init__(self,msg)

        self.done     = None
        self.connect("delete_event", self.delete_event)
        self.master = master
        self.set_usize(200,150)
        self.msg_lbl = gtk.GtkLabel(msg)
        self.ok_button = gtk.GtkButton('Okay')
        self.ok_button.connect('clicked', self.okay)
        self.action_area.pack_start(self.add_button,expand=gtk.FALSE)
        self.vbox.pack_start(self.msg_lbl)
        self.vbox.show_all()
        self.action_area.show_all()
        self.show()
        self.set_modal(gtk.TRUE)

    def okay(self,*args):
        self.done = gtk.TRUE

    def delete_event(win, event=None):
        ## self.hide()
        return gtk.FALSE

    def close(self,*args):
        self.hide()
        del self


class mainWindow(gtk.GtkWindow):         # Usual Base
    def __init__(self, title='pygtk app', jabberObj=None,
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

        self.jabberObj = jabberObj
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
        self.notebook.connect('switch_page', self.notebook_switched)
        self.box.pack_end(self.notebook, fill=gtk.TRUE, expand=gtk.TRUE)

        self._tabs.append( Roster_Tab(self, 'roster') )

        self.notebook.show()
        self.show()

    def handle_switch(self,*args):
        tab_no = self.notebook.get_current_page()
        self.getTab(tab_no).lowlight()
        
    def notebook_switched(self, *args):
        gtk.idle_add(self.handle_switch)
 
    def getTabs(self):
        return self._tabs

    def getTab(self,val):
        return self._tabs[val]

    def getSelectedTab(self):
        return self._tabs[self.notebook.get_current_page()]

    def addTab(self,tab_obj):
        self._tabs.append( tab_obj )
        return tab_obj

    def removeTab(self,tab):
        if type(tab) == type(1):
            self.notebook.remove_tab(tab)
            del self._tabs[tab]
        else:
            print "not yet implemented"
            
    def quit(self, *args):
        print "got exit ?"
        gtk.mainquit()


class jabberClient(jabber.Client):
    def __init__(self):

        not_connected = 1
        while not_connected:

            login_dia = Logon_dialog(None)
            while (login_dia.done is None):
                while gtk.events_pending(): gtk.mainiteration()
            login_dia.close()
        
            server   = login_dia.server
            username = login_dia.username
            password = login_dia.password
            resource = 'pygtkjab'

            print "connecting"
            jabber.Client.__init__(self,host=server,log='Dummy')
            try:
                self.connect()
            except xmlstream.error, e:
                print "Couldn't connect: %s" % e 
                sys.exit(0)
            else:
                print "Connected"
                
            print "logging in"
            if self.auth(username,password,resource):
                print "Logged in as %s to server %s" % ( username, server )
                not_connected = 0
            else:
                print "eek -> ", con.lastErr, con.lastErrCode
                sys.exit(1)



        print "requesting roster"
        ## Build the roster Tab ##
        self.roster = []
        r = self.requestRoster()
        self.gui = mainWindow("jabber app",jabberObj=self)
        self.sendInitPresence()                                  
        self.gui.getTab(0)._button.connect('clicked', self.addChatTabViaRoster )
        self.gui.getTab(0)._cb = self.addChatTabViaRoster;


    def dispatch_to_gui(self,obj):
        recieved = None
        for t in self.gui.getTabs():
            if t.recieve(obj): recieved = t
        return recieved

    def addChatTabViaRoster(self, *args):
        jid_raw = self.gui.getTab(0).get_roster_selection()
        if jid_raw:
            print jid_raw
            jid = jabber.JID(jid_raw)
            i = 0
            for t in self.gui.getTabs():
                print "comparing ", t.getJID() , jid.getStripped()
                if t.getJID() == jid.getStripped():
                    self.gui.notebook.set_page(i)
                    return
                i=i+1
            self.gui.addTab( Chat_Tab(self.gui, jid) )

            self.gui.getTab(-1)._send_button.connect('clicked',
                                                     self.messageSend,
                                                     self.gui.getTab(-1) )
            self.gui.getTab(-1)._entry.connect('activate',
                                                     self.messageSend,
                                                     self.gui.getTab(-1) )

    def messageSend(self, *args):
        tab = args[-1]
        msg = tab.getData()
        msg_obj = jabber.Message(tab._id, msg)
        msg_obj.setType('chat')
        self.send(msg_obj)


    def messageHandler(self, msg_obj):
        print msg_obj
        tab = self.dispatch_to_gui(msg_obj)
        if tab is None:
            self.gui.addTab(
                Chat_Tab(self.gui, msg_obj.getFrom())
                ).recieve(msg_obj)
            self.gui._tabs[-1]._send_button.connect('clicked',
                                                    self.messageSend,
                                                    self.gui._tabs[-1] )
            self.gui.getTab(-1)._entry.connect('activate',
                                                     self.messageSend,
                                                     self.gui.getTab(-1) )
            self.gui._tabs[-1].highlight()
        else:
            if tab != self.gui.getSelectedTab():
                tab.highlight()
                
    def presenceHandler(self, prs_obj):
        print "got presence 1"
        self.dispatch_to_gui(prs_obj)

    
    def process(self,time=0.1):
        while gtk.events_pending(): gtk.mainiteration()
        jabber.Client.process(self,time)
    

def main():

    s = jabberClient()
    while(1): s.process()
    
if __name__ == "__main__":
    main()  

















