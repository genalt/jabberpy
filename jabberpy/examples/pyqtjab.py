#!/usr/bin/python2

import sys
import string
from qt import *
import StringIO
import jabber
import time

from threading import *
from xml.sax import saxutils
from xml.sax import make_parser


def sendMessage (con, to, msg):
    msg = jabber.Message(to, msg)
    msg.setType('chat')
    print 'send ->', msg
    con.send(msg)

    
class DocumentList( QWidget ):
    def __init__( self, *args ):
        apply( QWidget.__init__, (self, ) + args )

        # 1 x 1
        self.mainGrid = QGridLayout( self, 1, 1, 5, 5 )

        self.listView = QListView( self )
        self.listView.addColumn('Document')

        self.listView.setSelectionMode( QListView.Extended )

        self.connect( self.listView, SIGNAL( 'clicked( QListViewItem* )' ), self.itemSelected )
        
        self.mainGrid.addWidget(self.listView, 1, 0)
        self.listView.setAllColumnsShowFocus( 1 )

           
    def itemSelected( self, item ):
        if item:
            item.setSelected( 1 )
            item.repaint()
            print item.text(0)
        
        def addDocument (self, docName):
            item = QListViewItem(self.listView)
            item.setText(0, docName)
                
class RosterList( QWidget ):
    def __init__( self, *args ):
        apply(QWidget.__init__, (self, ) + args )

        self.users = {}

        self.chatWindows = {}

        # 1 x 1
        self.mainGrid = QGridLayout( self, 1, 1, 5, 5 )

        self.listView = QListView( self )
        self.listView.addColumn('Handle')
        self.listView.addColumn('Status')
        self.listView.addColumn('Unread')
        self.listView.setSelectionMode( QListView.Extended )
        self.connect(self.listView, SIGNAL('clicked( QListViewItem* )' ), self.itemSelected )
        self.connect(self.listView, SIGNAL('rightButtonClicked (QListViewItem *, const QPoint &, int)'), self.rightClick)
        
        self.mainGrid.addWidget( self.listView, 1, 0 )
        self.listView.setAllColumnsShowFocus( 1 )

        self.rosterMenu = QPopupMenu(self)
        self.rosterMenu.insertItem('Add', self.queryAddUser)
        self.rosterMenu.insertItem('Remove', self.queryRemoveUser)

    
    def rightClick (self, item, point, i):
        self.rosterMenu.exec_loop(point, 0)

    def queryAddUser(self, userName):
        newUser = QInputDialog.getText('Add to roster',
                                       'Please enter handle of user to add', 'new user')
        if newUser and newUser[1]:
            if con:
                con.send(jabber.Presence(str(newUser[0]), 'subscribe'))

    def addUser (self, userName, status):
        if not self.users.has_key(userName):
            item = QListViewItem(self.listView)
            item.setText(0, userName)
            item.setText(1, status)
            item.setText(2, '0')
            self.users[userName] = item

    def queryRemoveUser (self, userName):
        pass

    def itemSelected( self, item ):
        if item:
            item.setSelected(1)
            item.repaint()
            to = str(item.text(0))
            cw = 0
            if self.chatWindows.has_key(to):
                cw = self.chatWindows[to]
            else:
                cw = ChatWindow()
                cw.peer = to
                cw.con = self.con
                self.tabWidget.addTab(cw, to)
                self.chatWindows[to] = cw

            self.users[to].setText(2, '0')

            if cw:
                self.tabWidget.showPage(cw)


class ChatWindow (QWidget):
    def __init__ (self, *args):
        apply(QWidget.__init__, (self, ) + args )

        self.widget = QWidget(self)
        self.mainGrid = QGridLayout(self.widget, 4, 2, 5, 5 )

        self.msgField = QLineEdit('', self.widget, 'MsgField')

        self.sendButton = QPushButton('&Send', self.widget, 'SendButton')
        self.clearButton = QPushButton('&Clear', self.widget, 'ClearButton')
        
        self.listView = QListView( self.widget )
        self.listView.setSelectionMode( QListView.Extended )
        self.listView.addColumn('Time')
        self.listView.addColumn('From')
        self.listView.addColumn('Message')
        self.label = QLabel('List of Messages', self.widget)
        
        self.mainGrid.addWidget(self.label, 0, 0)
        self.mainGrid.addMultiCellWidget(self.listView, 1, 1, 0, 1)
        self.mainGrid.addMultiCellWidget(self.msgField, 2, 2, 0, 1)
        self.mainGrid.addWidget(self.sendButton, 3, 0)
        self.mainGrid.addWidget(self.clearButton, 3, 1)
        self.listView.setAllColumnsShowFocus( 1 )

        self.connect(self.sendButton, SIGNAL('clicked( )' ), self.sendNewMessage )
        self.connect(self.clearButton, SIGNAL('clicked( )' ), self.clear )
        self.connect(self.msgField, SIGNAL('returnPressed( )' ), self.sendNewMessage )
        
        self.grid = QGridLayout(self, 1, 1, 5, 5)
        self.grid.addWidget(self.widget, 0, 0)

    def clear (self):
        if self.listView:
            self.listView.clear()

        if self.msgField:
            self.msgField.setText('')

    def addMsg (self, source, msg):
        item = QListViewItem(self.listView)
        item.setText(0, time.strftime('%X', time.localtime(time.time())))
        item.setText(1, source)
        item.setText(2, msg)        

    def sendNewMessage (self):
        if self.con and self.msgField.text() and self.peer:
            self.sendMessage(self.con, self.peer, str(self.msgField.text()));
            self.addMsg('me', self.msgField.text())
            self.msgField.setText('')


    def sendMessage (self, con, to, msg):
        msg = jabber.Message(to, msg)
        msg.setType('chat')
        print 'send ->', msg
        con.send(msg)

class AgentEditDialog (QTabWidget):
    def __init__ (self, parent, name, con, agentData):
        QTabWidget.__init__(self, parent, name)
        self.con = con
        self.agentData = agentData

        self.listView = QListView( self )
        self.listView.addColumn('Name')
        self.listView.addColumn('Value')

        print self.agentData

        for key in self.agentData.keys():
            item = QListViewItem(self.listView)
            item.setText(0, key)
            item.setText(1, self.agentData[key])

        name = 'noname'
        if self.agentData.has_key('name'):
            name = self.agentData['name']
        
        self.addTab(self.listView, name)
        
class AgentDialog (QTabDialog):
    def __init__ (self, parent, con):
        QTabDialog.__init__(self, parent, 'agents' )
        self.con = con

        self.listView = QListView( self )
        self.listView.addColumn('Agent')

        self.regInfo = con.requestRegInfo()
        #print con.getRegInfo()
        
        self.agents = con.requestAgents()
        for key in self.agents.keys():
            item = QListViewItem(self.listView)
            item.setText(0, key)

        self.addTab(self.listView, '&Agents')

        self.connect(self.listView, SIGNAL( 'clicked( QListViewItem* )' ), self.itemSelected )
        self.editWindows = {}

    def itemSelected( self, item ):
        key = str(item.text(0));
        if not self.editWindows.has_key(key):
            aed = AgentEditDialog(self, None, self.con, self.agents[str(item.text(0))])
            self.editWindows[key] = aed
            self.addTab(aed, key)

        self.showPage(self.editWindows[key])

        
class DocumentWindow (QMainWindow):
    def __init__ (self, con):
        QMainWindow.__init__( self, None, 'jyqt' )

        self.con = con

        self.initMenuBar()
        self.initWidgets()

        if self.con:
            self.con.setPresenceHandler(self.presenceCB)
            self.con.setMessageHandler(self.messageCB)
            self.statusBar().message('Connected')
            
        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL('timeout()'), self.timeout)
        self.timer.start(1000)

    def presenceCB(self, con, prs):
        who = str(prs.getFrom())
        i = string.find(who, '/')
        status = str(prs.getStatus())

        if i > 0:
            self.rosterList.addUser(who[:i], status)
        else:
            self.rosterList.addUser(who, status)
        
        who = str(prs.getFrom())
        type = prs.getType()
        if type == None:
            type = 'available'

        if type == 'subscribe':
            con.send(jabber.Presence(to=who, type='subscribed'))
            con.send(jabber.Presence(to=who, type='subscribe'))
        elif type == 'unsubscribe':
            con.send(jabber.Presence(to=who, type='unsubscribed'))
            con.send(jabber.Presence(to=who, type='unsubscribe'))


    def messageCB(self, con, msg):
        sender = str(msg.getFrom())

        i = string.find(sender, '/')
        if i > 0:
            sender = sender[:i]
        
        cw = 0
        if self.rosterList.chatWindows.has_key(sender):
            cw = self.rosterList.chatWindows[sender]
        else:
            cw = ChatWindow()
            cw.peer = sender
            cw.con = self.con
            self.tabWidget.addTab(cw, sender)
            self.rosterList.chatWindows[sender] = cw

        if cw:
            source = str(msg.getFrom())
            i = string.find(source, '/')
            if i:
                source = source[i+1:]
            
            cw.addMsg(source, str(msg.getBody()))
            #self.tabWidget.showPage(cw)
            
            tabBar = self.tabWidget.tabBar()
            tab = tabBar.tab(2)

        if self.rosterList.users and self.rosterList.users.has_key(sender):
            item = self.rosterList.users[sender]
            last = 0
            if item.text(2):
                s = str(item.text(2))
                if s:
                    last = int(s)
            item.setText(2, str(last + 1))

    def timeout(self):
        if self.con:
            self.con.process(0)

    def initMenuBar (self):
        self.fileMenu = QPopupMenu(self)
        self.menuBar().insertItem('&File', self.fileMenu)
        self.fileMenu.insertItem( '&About', self.about, Qt.Key_F1)
        self.fileMenu.insertItem( 'Quit', qApp, SLOT( 'quit()' ), Qt.CTRL + Qt.Key_Q )

        self.agentMenu = QPopupMenu(self)
        self.menuBar().insertItem('&Agents', self.agentMenu)
        self.agentMenu.insertItem( '&Edit', self.editAgents)

    def editAgents (self):
        if self.con:
            ad = AgentDialog(self, self.con)
            ad.show()

    def about(self):
        QMessageBox.about(self,'JYQT', 'JYQT 0.01 by www.elevenprospect.com')

    def initWidgets (self):
        self.tabWidget = QTabWidget(self)
        
        self.documentList = DocumentList(self)
        self.rosterList= RosterList(self)
        self.rosterList.con = con
        self.rosterList.tabWidget = self.tabWidget
        
        self.tabWidget.addTab(self.rosterList, '&Roster')
        self.tabWidget.addTab(self.documentList, '&Documents')
        
        self.setCentralWidget(self.tabWidget)

    def addDocument (self, docName):
        self.documentList.addDocument(docName)

userName = ''
password = ''
hostname = 'jabber.org'

for x in xrange(1, len(sys.argv)):
    if sys.argv[x] == '-u':
        userName = sys.argv[x + 1]

    if sys.argv[x] == '-p':
        password = sys.argv[x + 1]

    if sys.argv[x] == '-h':
        hostname = sys.argv[x + 1]

# jabber
con = None

if hostname:
    con = jabber.Client(host=hostname)
    if con:
        try:
            con.connect()
        except IOError, e:
            print e
    

if con and userName and password and con.auth(userName, password, 'default'):
    print 'connected'
else:
    con = None
    print 'not connected'

if con:
    con.requestRoster()
    con.sendInitPresence()
else:
    print 'not connected'

# setup QT
a = QApplication(sys.argv)
dw = DocumentWindow(con)
a.setMainWidget(dw)

# Start QT Window
dw.resize(500, 300)
dw.show()
a.exec_loop()

# disconnect
if con:
    con.disconnect()

