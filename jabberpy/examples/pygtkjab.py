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

        self.gui = gui
        
    def getID(self): return self._id;
    def setID(self,val): self._id = val;

    def recieve(self,obj): pass
    def setCallBack(self,cb): self._cb = cb
    def getCallBack(self): return self._cb 
    def getData(self): pass
    def setData(self,val): pass

    def _addToNoteBook(self):
        self._tab_label = gtk.GtkLabel(self._title)
        self._tab_label.show()
        self._notebook.append_page(self._box,self._tab_label)

    def tabClicked(self, *args):
        print "got it"
        return gtk.FALSE

    def highlight(self):
        style = self._tab_label.get_style()
        new_style = style.copy()
        new_style.fg[0] = self.cols['blue'] 
        self._tab_label.set_style(new_style)

    def lowlight(self):
        style = gtk.GtkLabel().get_style()
        new_style = style.copy()
        new_style.fg[0] = self.cols['black'] 
        self._tab_label.set_style(new_style)

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
        if obj.getFrom().getStripped() == self._title:
            if str(obj.__class__) == 'jabber.Message':
                self._txt.insert(None,self.cols['red'], None,
                                 "<%s> " % obj.getFrom().getStripped())
                self._txt.insert(None,None, None, "%s\n" % obj.getBody())
                return TRUE
            if str(obj.__class__) == 'jabber.Presence':
                if obj.getType() != 'unavailable':
                    self._txt.insert(None,self.cols['red'], None,
                                     "<%s> ( %s / %s )\n" % 
                                     ( obj.getFrom().getStripped(),
                                       obj.getStatus(), obj.getShow() ) )
                else:
                    self._txt.insert(None,self.cols['red'], None,
                                     "<%s> went offline\n" % 
                                     obj.getFrom().getStripped() )
                                       

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

        self._ctree = gtk.GtkCTree(1,0)
        self._ctree.set_column_width(0,200);
        self._ctree.set_line_style(gtk.CTREE_LINES_NONE)
        self._ctree.set_expander_style(gtk.CTREE_EXPANDER_CIRCULAR)
        self._ctree.connect("select_row" , self.rosterSelectCB)
        self.paint_tree()
        
        self._scroll.add(self._ctree)            

        self._scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.FALSE)
        self._box.pack_start(self._scroll, fill=gtk.TRUE, expand=gtk.TRUE)

        self._hbox = gtk.GtkHBox()
        self._button = gtk.GtkButton('Chat')
        self._hbox.pack_start(self._button, fill=gtk.FALSE, expand=gtk.FALSE)
        self._add_button = gtk.GtkButton('Add')
        self._hbox.pack_start(self._add_button, fill=gtk.FALSE,
                              expand=gtk.FALSE)

        self._box.pack_end(self._hbox, fill=gtk.TRUE, expand=gtk.FALSE)

        self._box.show_all()
        self._addToNoteBook()
    
    def rosterSelectCB(self, *args):
        self._roster_selected = self._ctree.get_row_data(int(args[1]))
        if args[3].type == GDK._2BUTTON_PRESS:
            self._cb()

    def get_roster_selection(self):
        return self._roster_selected

    def recieve(self,obj):
        if str(obj.__class__) != 'jabber.Message':
            if str(obj.__class__) == 'jabber.Iq':
                if obj.getQuery() == jabber.NS_ROSTER:
                    self.paint_tree() ## only paint if roster iq
            else:
                self.paint_tree() ## a presence 

    def paint_tree(self):
        print "DEBUG: rebuilding tree"
        self._ctree.clear()
        self._online_node = self._ctree.insert_node(
            None, None, ( 'online', ), 2,
            None, None, None, None, gtk.FALSE,
            gtk.TRUE )
        self._offline_node = self._ctree.insert_node(
            None, None, ( 'offline', ), 2,
            None, None, None, None, gtk.FALSE,
            gtk.TRUE )
        self._pending_node = self._ctree.insert_node(
            None, None, ( 'pending', ), 2,
            None, None, None, None, gtk.FALSE,
            gtk.TRUE )

        _roster = self.gui.jabberObj.getRoster()
        print _roster.getSummary()
        self._nodes = []
        for jid in _roster.getJIDs():
            attach_node = None
            if _roster.getOnline(jid) == 'online':
                attach_node = self._online_node
            elif _roster.getOnline(jid) == 'offline':
                attach_node = self._offline_node
            elif _roster.getOnline(jid) == 'pending':
                attach_node = self._pending_node
            else:
                pass
            node =self._ctree.insert_node(
                                 attach_node, None, ( str(jid), ), 2,
                                 None, None, None, None, gtk.TRUE,
                                 gtk.TRUE )
            self._nodes.append(node)
            self._ctree.node_set_row_data(node, str(jid))

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
        self.button_acc.connect('clicked', self.new_account)
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
        data = (rcfile.readline().splitlines())[0]
        self.server, self.username, self.password = data.split("\0")
        rcfile.close()
        return

    def new_account(self,*args):
        self.done = 2

    def delete_event(self, *args):
        gtk.mainquit()
        sys.exit(0)

    def close(self,*args):
        self.hide()
        del self

class New_ac_dialog(gtk.GtkWindow):                  
                                                 
    def __init__(self, master, jabber):

        gtk.GtkWindow.__init__(self)

        self.connect("delete_event", self.delete_event)
        self.master = master
        self.jabber = jabber
        self.done = None
        
        self.vbox = gtk.GtkVBox(gtk.FALSE,5)
        self.add(self.vbox)

        self.frame = gtk.GtkFrame("New Account")
        self.jabber.requestRegInfo()
        req = self.jabber.getRegInfo()

        self.table = gtk.GtkTable(6,6,gtk.FALSE)
        self.instr_lbl = gtk.GtkLabel(req[u'instructions'])
        
        self.entrys = {}
        i = 0
        for info in req.keys():
            if info != u'instructions' and \
               info != u'key':
                self.entrys[info] = {}
                self.entrys[info]['lbl'] = gtk.GtkLabel(info)
                self.entrys[info]['lbl'].set_alignment(1,0.5)
                self.entrys[info]['entry'] = gtk.GtkEntry()
                self.table.attach(
                    self.entrys[info]['lbl'], 0,2,1+i,2+i,
                    xpadding=3,ypadding=2)
                self.table.attach(
                    self.entrys[info]['entry'], 2,6,1+i,2+i,
                    xpadding=3,ypadding=2)
                i=i+1

        self.reg_button = gtk.GtkButton('Register')
        self.table.attach( self.reg_button, 2,6,0,1,xpadding=3,ypadding=2)
        self.reg_button.connect('clicked', self.register)

        self.frame.add(self.table)
        self.vbox.pack_start(self.frame)

        self.vbox.show_all()
        self.show()
        self.set_modal(gtk.TRUE)

    def register(self,*args):
        for info in self.entrys.keys():
            self.jabber.setRegInfo( info,
                                    self.entrys[info]['entry'].get_text() )
        self.username = self.entrys['username']['entry'].get_text()
        self.password = self.entrys['password']['entry'].get_text()
        self.jabber.sendRegInfo()
        self.done = gtk.TRUE

    def delete_event(win, event=None):
        self.hide()
        return gtk.TRUE

    def close(self,*args):
        self.hide()
        del self

class Add_dialog(gtk.GtkDialog):                  
                                                 
    def __init__(self, master, jabberObj):

        gtk.GtkDialog.__init__(self)

        self.jid_str  = None
        self.done     = None

        self.connect("delete_event", self.delete_event)
        self.master = master
        self.jabber = jabberObj
        
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

        self.done = self.jid_entry.get_text()


    def delete_event(win, event=None):
        self.hide()
        self.done = 1
        return gtk.FALSE

    def close(self,*args):
        self.hide()
        del self

MSG_DIA_TYPE_OK    = 0
MSG_DIA_TYPE_YESNO = 1
MSG_DIA_RET_OK     = 1
MSG_DIA_RET_CANCEL = 2

class Msg_dialog(gtk.GtkDialog):                  
                                                 
    def __init__(self, master, msg, type = MSG_DIA_TYPE_OK ):
        gtk.GtkDialog.__init__(self)

        self.done     = None
        self.connect("delete_event", self.delete_event)
        self.master = master
        self.set_usize(200,150)
        self.msg_lbl = gtk.GtkLabel(msg)
        
        self.ok_button = gtk.GtkButton('Ok')
        self.ok_button.connect('clicked', self.okay)
        self.action_area.pack_start(self.ok_button,expand=gtk.FALSE)

        if type == MSG_DIA_TYPE_YESNO:
            self.cancel_button = gtk.GtkButton('Cancel')
            self.cancel_button.connect('clicked', self.cancel)
            self.action_area.pack_start(self.cancel_button,expand=gtk.FALSE)
            
        self.vbox.pack_start(self.msg_lbl)
        self.vbox.show_all()
        self.action_area.show_all()
        self.show()
        self.set_modal(gtk.TRUE)

    def okay(self,*args):
        self.done = MSG_DIA_RET_OK

    def cancel(self,*args):
        self.done = MSG_DIA_RET_CANCEL

    def delete_event(win, event=None):
        self.hide()
        self.done = MSG_DIA_RET_CANCEL

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
        
        self.init_menu()        

        self.notebook = gtk.GtkNotebook()
        self.notebook.set_tab_pos (gtk.POS_BOTTOM);
        self.notebook.set_scrollable( gtk.TRUE ) 
        self.notebook.connect('switch_page', self.notebook_switched)
        self.box.pack_end(self.notebook, fill=gtk.TRUE, expand=gtk.TRUE)

        self._tabs.append( Roster_Tab(self, 'roster') )

        self.notebook.show()
        self.show()

    def init_menu(self):
        ag = gtk.GtkAccelGroup()
        self.itemf = gtk.GtkItemFactory(gtk.GtkMenuBar, "<main>", ag)
        self.add_accel_group(ag)
        
        self.itemf.create_items([
            ('/File',             None, None, 0, '<Branch>'),
            ('/File/Exit',        None, self.quit, 0, ''),
            ('/Roster',           None, None, 0, '<Branch>'),
            ('/Roster/Chat',      None, self.jabberObj.addChatTabViaRoster,
                                  1, ''),            
            ('/Roster/sep1',        None, None, 0, '<Separator>'),            
            ('/Roster/Add',        None, self.addCB, 1, ''),
            ('/Roster/Remove',     None, self.removeCB, 2, ''),
            ('/Tab',               None, None, 0, '<Branch>'),
            ('/Tab/Close',         None, self.closeTabCB, 1, ''),
            ('/Help', None, None, 0, '<Branch>') ,
            ('/Help/About', None, self.infoCB, 0, '')
            ])

        self.menubar = self.itemf.get_widget('<main>')
        self.box.pack_start(self.menubar, fill=gtk.FALSE, expand=gtk.FALSE)
        self.menubar.show()
    
    def addCB(self, *args):
        add_dia = Add_dialog(self, self.jabberObj )      
        while (add_dia.done is None):
            self.jabberObj.process()
        self.jabberObj.send(jabber.Presence(add_dia.done, 'subscribe'))
        add_dia.close()

    def removeCB(self,*args):
        who = self.getTab(0).get_roster_selection()
        if not who: return
        msg_dia = Msg_dialog(None,
                             "unsubscribe %s ?" % (who),
                             MSG_DIA_TYPE_YESNO
                             )
        while (msg_dia.done is None): self.jabberObj.process()
        if (msg_dia.done == MSG_DIA_RET_OK):
            self.jabberObj.send(jabber.Presence(to=who, type='unsubscribe'))
        msg_dia.close()

    def closeTabCB(self, *args):
        if self.notebook.get_current_page():
            self.getSelectedTab().destroy()

    def findCB(self, *args): pass
    def infoCB(self, *args): pass

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
        gtk.mainquit()
        sys.exit(0)

class jabberClient(jabber.Client):
    def __init__(self):

        not_connected = 1
        while not_connected:

            login_dia = Logon_dialog(None)
            while (login_dia.done is None):
                while gtk.events_pending(): gtk.mainiteration()
            login_dia.close()

            server   = login_dia.server

            print "connecting"
            jabber.Client.__init__(self,host=server,debug=1)
            try:
                self.connect()
            except:
                msg_dia = Msg_dialog(None, "Couldnt connect to "+server)
                while (msg_dia.done is None):
                    while gtk.events_pending(): gtk.mainiteration()
                msg_dia.close()
                sys.exit(0)
            else:
                print "Connected"

            if (login_dia.done == 2):
                new_acc_dia = New_ac_dialog(None, self)
                while (new_acc_dia.done is None):
                    self.process()
                new_acc_dia.close()
                username = new_acc_dia.username
                password = new_acc_dia.password

            else:
                username = login_dia.username
                password = login_dia.password
            resource = 'pygtkjab'

                
            print "logging in"
            if self.auth(username,password,resource):
                print "Logged in as %s to server %s" % ( username, server )
                not_connected = 0
            else:
                msg_dia = Msg_dialog(None, self.lastErr)
                while (msg_dia.done is None):
                    while gtk.events_pending(): gtk.mainiteration()
                msg_dia.close()
                #print "eek -> ", self.lastErr, self.lastErrCode
                sys.exit(1)


        print "requesting roster"
        ## Build the roster Tab ##
        self.roster = []
        r = self.requestRoster()
        self.gui = mainWindow("jabber app",jabberObj=self)
        self.sendInitPresence()                                  
        self.gui.getTab(0)._button.connect('clicked',
                                           self.addChatTabViaRoster )
        self.gui.getTab(0)._add_button.connect('clicked',
                                               self.addToRoster )

        self.gui.getTab(0)._cb = self.addChatTabViaRoster;

        self._unsub_lock = 0 ## hack to fix unsubscribe wierdo bug

    def addToRoster(self, *args): pass
              
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

        type = prs_obj.getType()
        who  = prs_obj.getFrom().getStripped()

        print "DEBUG: pres got %s from %s" % ( type, who )
        print "DEBUG: %s" % prs_obj

        if type == 'subscribe':
            msg_dia = Msg_dialog(None,
                                 "subscribe request from %s" % (who),
                                 MSG_DIA_TYPE_YESNO
                                 )
            while (msg_dia.done is None): self.process()
            if (msg_dia.done == MSG_DIA_RET_OK):
                self.send(jabber.Presence(to=who, type='subscribed'))
                
                if who not in self.getRoster().getJIDs() or \
                   self.getRoster().getSub(who) != 'both':
                    self.send(jabber.Presence(to=who, type='subscribe'))
            msg_dia.close()

        elif type == 'unsubscribe' and not self._unsub_lock:
            self._unsub_lock = 1 ## HACK !
            msg_dia = Msg_dialog(None,
                                 "unsubscribe request from %s" % (who),
                                 MSG_DIA_TYPE_YESNO
                                 )
            while (msg_dia.done is None): self.process()
            if (msg_dia.done == MSG_DIA_RET_OK):
                self.send(jabber.Presence(to=who, type='unsubscribed'))
            msg_dia.close()
            self._unsub_lock = 0

        else: pass

        self.dispatch_to_gui(prs_obj)

    def iqHandler(self, iq_obj):
        print "got iq", iq_obj.getQuery()
        self.dispatch_to_gui(iq_obj)

    def process(self,time=0.1):
        while gtk.events_pending(): gtk.mainiteration()
        jabber.Client.process(self,time)
    

def main():

    s = jabberClient()
    while(1): s.process()
    
if __name__ == "__main__":
    main()  

















