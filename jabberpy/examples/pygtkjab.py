#!/usr/bin/env python2

#
# TODO:
#   -- fix mass transport subscribe crash ??
#   -- implement group chat
#   -- catch errors better with dialog to show em.
#

import gtk, _gtk, GDK
import jabber
import sys,string,os,re

TRUE = 1
FALSE = 0
OK = 1
CANCEL = 2

## add a server name entry to the below ## 
Known = {
          'yahoo':
             { 'xpm' : 'an xpm path' },
          'msn':
             { 'xpm' : 'info....'},
          'icq':
             { 'xpm' : 'info....'},
        }

def makeKnownNice(jid):
    for known in Known.keys():
        if re.match("^"+known+".*", jid.getDomain()):
            if jid.getNode():
                return jid.getNode()
            else:
                return known + " transport"
    return str(jid)

def sort_jids(a,b):
    if string.lower(str(a)) < string.lower(str(b)): return -1
    if string.lower(str(a)) > string.lower(str(b)): return 1
    return 0
    
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
        self.cols['black'] = self.cmap.alloc('black')
        self.cols['green'] = self.cmap.alloc('green')

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
        #style = _gtk.gtk_rc_get_style() # self._tab_label)
        style = self._tab_label.get_style()
        new_style = style.copy()
        new_style.fg[0] = self.cols['blue'] 
        self._tab_label.set_style(new_style)

    def lowlight(self):
        style = self._tab_label.get_style()
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
    def __init__(self, gui, jid, title='a tab'):
        Tab.__init__(self, gui, title)

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
        if obj.getFrom().getStripped() == self._id:
            if str(obj.__class__) == 'jabber.Message':
                if obj.getError():
                    err_code = ''
                    if obj.getErrorCode(): err_code = obj.getErrorCode()
                    self._txt.insert(None,self.cols['red'], None,
                                     "%s ( %s )" % (obj.getError(),
                                     err_code) )
                else:
                    self._txt.insert(None,self.cols['red'], None,
                                     "<%s> " % obj.getFrom().getStripped())
                    self._txt.insert(None,None, None, "%s\n" % obj.getBody())
                return TRUE
            if str(obj.__class__) == 'jabber.Presence':
                if obj.getType() != 'unavailable':
                    self._txt.insert(None,self.cols['green'], None,
                                     "<%s> ( %s / %s )\n" % 
                                     ( obj.getFrom().getStripped(),
                                       obj.getStatus(), obj.getShow() ) )
                else:
                    self._txt.insert(None,self.cols['green'], None,
                                     "<%s> went offline\n" % 
                                     obj.getFrom().getStripped() )
                return TRUE
        return FALSE
    
    def getData(self):
        txt = self._entry.get_text() 
        self._entry.set_text('')
        self._txt.insert(None,None,None, "<%s> %s\n" %
                         ( self.gui.jabberObj.loggedin_jid.getStripped(), txt)
                         )
        return txt

class Url_Tab(Tab): ### Make bigger and Better !!!
    def __init__(self, gui):
        Tab.__init__(self, gui, 'URLs')

        self._id = 'URLs'
        self._regexp = re.compile('(http://[^\s]+)', re.IGNORECASE)

        self._scrolled_win = gtk.GtkScrolledWindow()
        self._scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._box.pack_start(self._scrolled_win)


        self._list = gtk.GtkList()
        self._list.set_selection_mode(gtk.SELECTION_BROWSE)
        self._scrolled_win.add_with_viewport(self._list)


        self._list.connect("select-child" , self.selectCB)


        self._hbox = gtk.GtkHBox()
        self._open_button = gtk.GtkButton('open')
        self._hbox.pack_end(self._open_button, fill=gtk.FALSE,
                            expand=gtk.FALSE)
        self._box.pack_end(self._hbox, fill=gtk.TRUE, expand=gtk.FALSE)
        self._box.show_all()
        self._addToNoteBook()

        ## this_tab.event_connected = 0 ??

    def getJID(self):
        return self._id


    def recieve(self,obj):
        if str(obj.__class__) == 'jabber.Message':
            m = self._regexp.match(obj.getBody())
            if m:
                list_item = gtk.GtkListItem(m.group())
                self._list.add(list_item)
                list_item.show()
                return TRUE
        return FALSE
    
    def selectCB(self, *args): pass


class Roster_Tab(Tab): ### Make bigger and Better !!!
    def __init__(self, gui, title):
        Tab.__init__(self, gui, title)
        self._roster_selected = None
        self._online_icon, self._online_mask = \
          gtk.create_pixmap_from_xpm( gui.get_window(), None,"online.xpm" );
        self._offline_icon, self._offline_mask = \
          gtk.create_pixmap_from_xpm( gui.get_window(), None,"offline.xpm" );
        self._pending_icon, self._pending_mask = \
          gtk.create_pixmap_from_xpm( gui.get_window(), None,"pending.xpm" );

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
        self._ctree.freeze()
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
        jids = _roster.getJIDs()
        jids.sort(sort_jids)
        for jid in jids:
            attach_node = None
            nice_name = makeKnownNice(jid)
            show = ''
            if _roster.getShow(jid): show = _roster.getShow(jid)
            if _roster.getStatus(jid):
                if show:
                    show = " ( %s / %s )" % ( show, _roster.getStatus(jid) )
                else:
                    show = " ( %s )" % _roster.getStatus(jid) 
            nice_name = str("%s %s" % ( nice_name, show ))
            print "DEBUG: %s" % nice_name
            if _roster.getOnline(jid) == 'online':
                node =self._ctree.insert_node(
                                 self._online_node, None, ( nice_name, )
                                 , 2,
                                 pixmap_closed = self._online_icon,
                                 mask_closed   = self._online_mask,
                                 is_leaf=gtk.TRUE,
                                 expanded=gtk.TRUE )

            elif _roster.getOnline(jid) == 'offline':
                node =self._ctree.insert_node(
                                 self._offline_node, None, ( nice_name, )
                                 , 2,
                                 pixmap_closed = self._offline_icon,
                                 mask_closed   = self._offline_mask,
                                 is_leaf=gtk.TRUE,
                                 expanded=gtk.TRUE )

            elif _roster.getOnline(jid) == 'pending':
                node =self._ctree.insert_node(
                                 self._pending_node, None, ( nice_name, )
                                 , 2,
                                 pixmap_closed = self._pending_icon,
                                 mask_closed   = self._pending_mask,
                                 is_leaf=gtk.TRUE,
                                 expanded=gtk.TRUE )
            else:
                pass

            self._nodes.append(node)
            self._ctree.node_set_row_data(node, str(jid))
            
        self._ctree.thaw()
        
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
                                                 
    def __init__(self, master, jabber, agent=None):

        gtk.GtkWindow.__init__(self)

        self.connect("delete_event", self.delete_event)
        self.master = master
        self.jabber = jabber
        self.done = None
        self.agent = agent
        self.vbox = gtk.GtkVBox(gtk.FALSE,5)
        self.add(self.vbox)

        self.frame = gtk.GtkFrame("New Account")
        self.jabber.requestRegInfo(self.agent)
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
        self.jabber.sendRegInfo(self.agent)
        self.done = OK

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

class Status_dialog(gtk.GtkDialog):                  
                                                 
    def __init__(self):

        gtk.GtkDialog.__init__(self)

        self.jid_str  = None
        self.done     = None
        self.type     = 'available'

        self.connect("delete_event", self.delete_event)
        #self.master = master
        #self.jabber = jabberObj
        
        self.set_usize(200,150)

        self.table = gtk.GtkTable(5,2,gtk.FALSE)
        self.jid_lbl = gtk.GtkLabel('Status')

        self.jid_entry   = gtk.GtkEntry()

        self.table.attach( self.jid_lbl,     0,1,0,1)
        self.table.attach( self.jid_entry,   1,2,0,1)

        self.add_button = gtk.GtkButton('Set')
        self.add_button.connect('clicked', self.set)
        self.action_area.pack_start(self.add_button,expand=gtk.FALSE)

        self.avail_radio   = gtk.GtkRadioButton(None, 'available')
        self.unavail_radio = gtk.GtkRadioButton(self.avail_radio, 'unavailable')
        self.avail_radio.connect('clicked', self.avail)
        self.unavail_radio.connect('clicked', self.unavail)
        self.avail_radio.set_active(gtk.TRUE)

        self.table.attach( self.avail_radio,     0,2,1,2)
        self.table.attach( self.unavail_radio,   0,2,2,3)

        self.vbox.pack_start(self.table)
             
        self.vbox.show_all()
        self.action_area.show_all()
        self.show()
        self.set_modal(gtk.TRUE)

    def avail(self, *args): self.type = None
    def unavail(self, *args): self.type = 'unavailable'

    def set(self,*args):

        self.done =  ( self.type , self.jid_entry.get_text() )
        

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

class Trans_dialog(gtk.GtkDialog):                  
                                                 
    def __init__(self, master, jabberObj ):
        gtk.GtkDialog.__init__(self)

        self.agents = jabberObj.requestAgents()

        self.done     = None
        self.connect("delete_event", self.delete_event)
        self.master = master
        self.set_usize(200,150)
        
        self.ok_button = gtk.GtkButton('Ok')
        self.ok_button.connect('clicked', self.okay)
        self.action_area.pack_start(self.ok_button,expand=gtk.FALSE)
        self.cancel_button = gtk.GtkButton('Cancel')
        self.cancel_button.connect('clicked', self.cancel)
        self.action_area.pack_start(self.cancel_button,expand=gtk.FALSE)

        self.scrolled_win = gtk.GtkScrolledWindow()
        self.scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox.pack_start(self.scrolled_win)

        self.list = gtk.GtkList()
        self.list.set_selection_mode(gtk.SELECTION_BROWSE)
        self.scrolled_win.add_with_viewport(self.list)

        for i in self.agents.keys():
            if self.agents[i].has_key('transport'):
                list_item = gtk.GtkListItem(self.agents[i]['name'])
                list_item.set_data('jid', i)
                self.list.add(list_item)
                list_item.show()

        self.list.connect("select-child" , self.selectCB)
            
        self.vbox.pack_start(self.scrolled_win)
        self.vbox.show_all()
        self.action_area.show_all()
        self.show()
        self.selected = None
        self.set_modal(gtk.TRUE)

    def selectCB(self, *args):
        self.selected = args[1].get_data('jid')

    def okay(self,*args):
        self.done = OK

    def cancel(self,*args):
        self.done = CANCEL

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
        self.tbox = gtk.GtkHBox()

        self.checkItemCalled = 0
        self.init_menu()
        self.init_status_select()

        self.close_but = gtk.GtkButton('X')
        self.close_but.connect("clicked", self.closeTabCB);
        self.close_but.show()
        self.tbox.pack_end(self.close_but, fill=gtk.FALSE, expand=gtk.FALSE)
        
        self.tbox.show()
        self.box.pack_start(self.tbox, fill=gtk.FALSE, expand=gtk.FALSE)
        
        self.notebook = gtk.GtkNotebook()
        self.notebook.set_tab_pos (gtk.POS_BOTTOM);
        self.notebook.set_scrollable( gtk.TRUE ) 
        self.notebook.connect('switch_page', self.notebook_switched)
        self.box.pack_end(self.notebook, fill=gtk.TRUE, expand=gtk.TRUE)

        self._tabs.append( Roster_Tab(self, 'roster') )

        self.notebook.show()
        self.show()


    def init_status_select(self):
        ag = gtk.GtkAccelGroup()
        self.itemsel = gtk.GtkItemFactory(gtk.GtkOptionMenu, "<select>", ag)
        self.add_accel_group(ag)
        
        self.itemsel.create_items([
            ('/Available',   None, self.statusCB, 1,     ''),
            ('/Unavailable', None, self.statusCB, 0,     ''),
            ('/Custom',      None, self.custstatusCB, 0, ''),
            ])

        self.status_select = self.itemsel.get_widget('<select>')
        self.tbox.pack_start(self.status_select,
                             fill=gtk.TRUE, expand=gtk.TRUE)
        self.status_select.show()

    def init_menu(self):
        ag = gtk.GtkAccelGroup()
        self.itemf = gtk.GtkItemFactory(gtk.GtkMenuBar, "<main>", ag)
        self.add_accel_group(ag)
        
        self.itemf.create_items([
            ('/File',             None, None, 0, '<Branch>'),
            ('/File/Exit',        None, self.quit, 0, ''),
            ('/Tools',            None, None, 0, '<Branch>'),
            ('/Tools/Chat',       None, self.jabberObj.addChatTabViaRoster,
                                  1, ''),            
            ('/Tools/sep1',       None, None, 0, '<Separator>'),            
            ('/Tools/Add',        None, self.addCB, 1, ''),
            ('/Tools/Remove',     None, self.removeCB, 0, ''),

            ('/Tools/Status/Available',   None, self.statusCB, 1, '<CheckItem>'),
            ('/Tools/Status/Unavailable', None, self.statusCB, 0, '<CheckItem>'),
            ('/Tools/Status/Custom', None, self.custstatusCB, 0, ''),
            ('/Tools/sep2',        None, None, 0, '<Separator>'),            
            ('/Tools/Transports', None, self.transCB, 0, ''),
            ('/Tools/Tabs/Rotate', None, self.rotateTabCB, 0, ''),
            ('/Tools/Tabs/Url Grabber', None, self.urlTabCB, 0, ''),
            ('/Help', None, None, 0, '<Branch>') ,
            ('/Help/About', None, self.infoCB, 0, '')
            ])

        self.menubar = self.itemf.get_widget('<main>')
        self.itemf.get_widget( '/Tools/Status/Available' ).set_active(gtk.TRUE)
        self.tbox.pack_start(self.menubar, fill=gtk.TRUE, expand=gtk.TRUE)
        self.menubar.show()

    def statusCB(self,action,widget):
        if self.checkItemCalled == 1:   ## Make sure set_active does not 
            return                      ## recall the callback
        self.checkItemCalled = 1;

        ## More nasty workarounds for ItemFactory Radiobutton problems
        for path in [ '/Tools/Status/Available', '/Tools/Status/Unavailable' ]:
            if widget != self.itemf.get_widget( path ):
                self.itemf.get_widget( path ).set_active(gtk.FALSE)
        self.checkItemCalled = 0;
        
        if action == 1:
            # available
            self.jabberObj.presence_details = [ 'available', None ]
            pres = jabber.Presence()
        else:
            self.jabberObj.presence_details = [ 'unavailable', None ]
            pres = jabber.Presence(type='unavailable')

        self.jabberObj.send(pres)
            
    def custstatusCB(self, *args):
        dia = Status_dialog()
        while dia.done is None:
            self.jabberObj.process()
        type, show = dia.done
        pres = jabber.Presence(type=type)
        pres.setShow(show)
        self.jabberObj.presence_details = [ type, show ]
        self.jabberObj.send(pres)
        dia.close()
        
    def urlTabCB(self, *args):
        url_tab = self.findTab( 'URLs' )
        if url_tab:
            url_tab.destroy()            
        else:
            self._tabs.append( Url_Tab(self) )

    def rotateTabCB(self, *args):
        if self.notebook.get_tab_pos() == gtk.POS_BOTTOM:
            self.notebook.set_tab_pos( gtk.POS_LEFT )
        else:
            self.notebook.set_tab_pos( gtk.POS_BOTTOM )

    def transCB(self, *args):
        trans_dia = Trans_dialog(None, self.jabberObj)
        while (trans_dia.done is None):
            self.jabberObj.process()
        if trans_dia.done == OK and trans_dia.selected:
            print "SELECTED %s" % trans_dia.selected
            names = string.split(trans_dia.selected, '.')
            agent = names[0]
            trans_dia.close()
            new_acc_dia = New_ac_dialog(None, self.jabberObj, agent=agent)
            while (new_acc_dia.done is None):
                self.jabberObj.process()
            new_acc_dia.close()
            return
        trans_dia.close()
    
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

    def findTab(self,id):
        for tab in self._tabs:
            if tab._id == id: return tab
        return None
 
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
        #gtk.mainquit()
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

        self.loggedin_jid     = jabber.JID( node = username, domain = server,
                                        resource = resource );
        self.presence_details = [ 'available', None ]
        
        Known[server] = { 'xpm':'something' }
        
        print "requesting roster"
        ## Build the roster Tab ##
        self.roster = []
        r = self.requestRoster()
        self.gui = mainWindow("jabber app",jabberObj=self)
        self.gui.getTab(0)._cb = self.addChatTabViaRoster;
        self.sendInitPresence()                                  
        self._unsub_lock = 0 ## hack to fix unsubscribe wierdo bug
        self._pres_queue  = []

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
            self.gui.addTab( Chat_Tab(self.gui, jid, makeKnownNice(jid) ) )

            self.gui.getTab(-1)._send_button.connect('clicked',
                                                     self.messageSend,
                                                     self.gui.getTab(-1) )
            self.gui.getTab(-1)._entry.connect('activate',
                                                     self.messageSend,
                                                     self.gui.getTab(-1) )
            self.gui.notebook.set_page(i)
            
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
                Chat_Tab(self.gui, msg_obj.getFrom(),
                         makeKnownNice(msg_obj.getFrom()) )
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


        else: pass

        self.dispatch_to_gui(prs_obj)
        self._unsub_lock = 0

    def iqHandler(self, iq_obj):
        print "got iq", iq_obj.getQuery()
        self.dispatch_to_gui(iq_obj)

    def process(self,time=0.1):
        while gtk.events_pending(): gtk.mainiteration()
        jabber.Client.process(self,time)
    

def main():

#    pass args to jabberClient object
#    if -f exists mkfifo named with f param, open for writing ( r+ )
#    launcher will open this for reading after forking the app
#    app will then pipe messages to it

    s = jabberClient()
    while(1): s.process()
    
if __name__ == "__main__":
    main()  

















