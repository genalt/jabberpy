#!/usr/bin/env python2.2
# we require Python 2.2 because PyPicoGUI does

import PicoGUI
import socket
from select import select
from string import split,strip,join
import sys,os
import jabber

True = 1
False = 0

pg_roster = {}
log_chat_format = '<%(from)s> %(body)s'
log_st_format = '*%(from)s %(type)s: %(body)s'

def getBuddy(jid):
    jid = str(jid)
    if not pg_roster.has_key(jid):
        buddy = Buddy(jid)
        pg_roster[jid] = buddy
    return pg_roster[jid]

class Buddy(object):
    def __init__(self, jid):
        self.jid = jid
        self.item = status_item.addWidget('ListItem')
        self.item.text = jid
        self.listed = False
        self._log = []
        global app
        app.link(self.select, self.item, 'activate')

    def select(self, *a):
        global Who
        Who = self.jid
        self.update_log_box()

    def update_log_box(self):
        log_box.text = '\n'.join(self._log)
        app.server.update()

    def log(self, msgdata):
        if msgdata.get('type', 'chat') == 'chat':
            self._log.append(log_chat_format % msgdata)
        else:
            self._log.append(log_st_format % msgdata)
        if Who == self.jid:
            self.update_log_box()

pg_log_data = []
def pg_log(text):
    global log_to_stdout, log_box
    if log_to_stdout:
        print text
    pg_log_data.append(text)
    if not Who:
        log_box.text = '\n'.join(pg_log_data)

# PicoGUI initialization

app = PicoGUI.Application('Jabber client')
roster_box = app.addWidget('Box')
roster_box.side = 'left'
roster_box.transparent = 1
roster_box.sizemode = 'percent'
roster_box.size = '20'
panelbar = roster_box.addWidget('PanelBar')
panelbar.side = 'left'
panelbar.bind = roster_box
status_item = roster_box.addWidget('ListItem', 'inside')
status_item.text = '(status)'
status_item.hilighted = 1
roster_box.addWidget('Scroll', 'inside').bind = roster_box
log_box = panelbar.addWidget('TextBox')
log_box.side = 'right'
log_box.sizemode = 'percent'
log_box.size = 100
log_box.autoscroll = 1
panelbar.addWidget('Scroll').bind = log_box
entry = panelbar.addWidget('Field')
entry.side = 'bottom'
def select_status(*a):
    global Who, log_box
    Who = ''
    log_box.text = '\n'.join(pg_log_data)
    app.server.update()
select_status()
app.link(select_status, status_item, 'activate')

def pg_input(message, initial='', password=0):
    global app
    s = app.server
    s.mkcontext()
    dlg = PicoGUI.Widget(s, s.mkpopup(-1, -1, 0, 0))
    msg = dlg.addWidget('Label', 'inside')
    msg.text = message
    field = msg.addWidget('Field')
    field.text = initial
    if password == 1: password = '*'
    if type(password) == type(''): password = ord(password)
    field.password = password
    s.focus(dlg)
    s.focus(field)
    def finish(*a):
        app.send(app, 'stop')
    app.link(finish, field, 'activate')
    app.run()
    txt = s.getstring(field.text)[:-1]
    s.rmcontext()
    return txt

# Console and jabber initialization

# Change this to 0 if you dont want a color xterm
USE_COLOR = 0

Who = ''
MyStatus = ''
MyShow   = ''

def usage():
    pg_log("%s: a simple python jabber client " % sys.argv[0])
    pg_log("usage:")
    pg_log("%s <server> - connect to <server> and register" % sys.argv[0])
    pg_log("%s <server> <username> [<resource>]"    % sys.argv[0])
    pg_log("%s <username>@<server> [<resource>]"    % sys.argv[0])
    pg_log("            - connect to server and login   ")
    sys.exit(0)


def doCmd(con,txt):
    global Who
    cmd = split(txt)
    if cmd[0] == 'presence':
        to = cmd[1]
        type = cmd[2]
        con.send(jabber.Presence(to, type))
    elif cmd[0] == 'status':
        p = jabber.Presence()
        MyStatus = ' '.join(cmd[1:])
        p.setStatus(MyStatus)
        con.send(p)
    elif cmd[0] == 'show':
        p = jabber.Presence()
        MyShow = ' '.join(cmd[1:])
        p.setShow(MyShow)
        con.send(p)
    elif cmd[0] == 'subscribe':
        to = cmd[1]
        con.send(jabber.Presence(to, 'subscribe'))
    elif cmd[0] == 'unsubscribe':
        to = cmd[1]
        con.send(jabber.Presence(to, 'unsubscribe'))
    elif cmd[0] == 'roster':
        con.requestRoster()
        _roster = con.getRoster()
        for jid in _roster.getJIDs():
            pg_log(colorize("%s :: %s (%s/%s)"
                           % ( jid, _roster.getOnline(jid),
                               _roster.getStatus(jid),
                               _roster.getShow(jid),
                               ) , 'blue' ))

    elif cmd[0] == 'agents':
        pg_log(`con.requestAgents()`)
    elif cmd[0] == 'register':
        agent = ''
        if len(cmd) > 1:
            agent = cmd[1]
        con.requestRegInfo(agent)
        pg_log(`con.getRegInfo()`)
    elif cmd[0] == 'exit':
        con.disconnect()
        pg_log(colorize("Bye!",'red'))
        sys.exit(0)
    elif cmd[0] == 'help':
        pg_log("commands are:")
        pg_log("   subscribe <jid>")
        pg_log("      - subscribe to jid's presence")
        pg_log("   unsubscribe <jid>")
        pg_log("      - unsubscribe to jid's presence")
        pg_log("   agents")
        pg_log("      - list agents")
        pg_log("   register <agent>")
        pg_log("      - register with an agent")
        pg_log("   presence <jabberid> <type>")
        pg_log("      - sends a presence of <type> type to the jabber id")
        pg_log("   status <status>")
        pg_log("      - set your presence status message")
        pg_log("   show <status>")
        pg_log("      - set your presence show message")
        pg_log("   roster")
        pg_log("      - requests roster from the server and ")
        pg_log("        display a basic dump of it.")
        pg_log("   exit")
        pg_log("      - exit cleanly")
    else:
        pg_log(colorize("uh?", 'red'))

def doSend(con,txt):
    global Who
    if Who != '':
        msg = jabber.Message(Who, txt.strip())
        msg.setType('chat')
        #pg_log("<%s> %s" % (JID, msg.getBody()))
        con.send(msg)
        buddy = getBuddy(Who)
        buddy.log({'from':JID, 'to':Who, 'body':txt.strip()})
    else:
        pg_log(colorize('Nobody selected','red'))
            

def messageCB(con, msg):
    """Called when a message is recieved"""
    mfrom = msg.getFrom()
    mbody = msg.getBody()
    buddy = getBuddy(mfrom)
    buddy.log({'from':mfrom, 'to':JID, 'body':mbody})

def presenceCB(con, prs):
    """Called when a presence is recieved"""
    who = prs.getFrom()
    type = prs.getType()
    if type == None: type = 'available'

    # subscription request: 
    # - accept their subscription
    # - send request for subscription to their presence
    if type == 'subscribe':
        pg_log(colorize("subscribe request from %s" % (who), 'blue'))
        con.send(jabber.Presence(to=str(who), type='subscribed'))
        con.send(jabber.Presence(to=str(who), type='subscribe'))

    # unsubscription request: 
    # - accept their unsubscription
    # - send request for unsubscription to their presence
    elif type == 'unsubscribe':
        pg_log(colorize("unsubscribe request from %s" % (who), 'blue'))
        con.send(jabber.Presence(to=str(who), type='unsubscribed'))
        con.send(jabber.Presence(to=str(who), type='unsubscribe'))

    elif type == 'subscribed':
        pg_log(colorize("we are now subscribed to %s" % (who), 'blue'))

    elif type == 'unsubscribed':
        pg_log(colorize("we are now unsubscribed to %s"  % (who), 'blue'))

    elif type == 'available':
        sta = '%s / %s' % (prs.getShow(), prs.getStatus())
        pg_log(colorize("%s is available (%s)" % (who, sta),'blue'))
        buddy = getBuddy(who)
        buddy.listed = True
        buddy.item.text = '%s (%s)' % (who, sta)
        buddy.log({'type':'available', 'from':who, 'body':sta})
        app.server.update()
    elif type == 'unavailable':
        sta = '%s / %s' % (prs.getShow(), prs.getStatus())
        pg_log(colorize("%s is unavailable (%s)" % (who, sta),'blue'))
        buddy = getBuddy(who)
        app.server.attachwidget(0, buddy.item, 0)
        buddy.listed = False
        buddy.log({'type':'unavailable', 'from':who, 'body':sta})
        app.server.update()


def iqCB(con,iq):
    """Called when an iq is recieved, we just let the library handle it at the moment"""
    pass

def disconnectedCB(con):
    pg_log(colorize("Ouch, network error", 'red'))
    sys.exit(1)

def colorize(txt, col):
    """Return colorized text"""
    if not USE_COLOR: return txt ## DJ - just incase it breaks your terms ;) ##
    cols = { 'red':1, 'green':2, 'yellow':3, 'blue':4}
    initcode = '\033[;3'
    endcode  = '\033[0m'
    if type(col) == type(1): 
        return initcode + str(col) + 'm' + txt + endcode
    try: return initcode + str(cols[col]) + 'm' + txt + endcode
    except: return txt


if len(sys.argv) == 1: usage()

argv = sys.argv

if '-d' in argv:
    log_to_stdout = True
    argv.remove('-d')
else:
    log_to_stdout = False

if argv[1].find('@') != -1:
    arg_tmp = sys.argv[1].split('@')
    arg_tmp.reverse()
    argv[1:2] = arg_tmp
    del arg_tmp

Server = argv[1]
Username = ''
Password = ''
Resource = 'default'

con = jabber.Client(host=Server,debug=False,log=None)

# Experimental SSL support
#
# con = jabber.Client(host=Server,debug=True ,log=sys.stderr,
#                    port=5223, connection=xmlstream.TCP_SSL)

try:
    con.connect()
except IOError, e:
    pg_log("Couldn't connect: %s" % e)
    sys.exit(0)
else:
    pg_log(colorize("Connected",'red'))

con.setMessageHandler(messageCB)
con.setPresenceHandler(presenceCB)
con.setIqHandler(iqCB)
con.setDisconnectHandler(disconnectedCB)

if len(argv) == 2:
    # Set up a jabber account
    con.requestRegInfo()
    req = con.getRegInfo()
    pg_log(req[u'instructions'])
    for info in req.keys():
        if info != u'instructions' and \
           info != u'key':
            pg_log("enter %s;" % info)
            con.setRegInfo( info,strip(sys.stdin.readline()) )
    con.sendRegInfo()
    req = con.getRegInfo()
    Username = req['username']
    Password = req['password']
else:
    Username = argv[2]
    Password = pg_input('Password for %s:' % Username, password='*')
    if len(argv) > 3:
        Resource = argv[3]
    else:
        Resource = 'PyPguiJab'

pg_log(colorize("Attempting to log in...", 'red'))


if con.auth(Username,Password,Resource):
    pg_log(colorize("Logged in as %s to server %s" % ( Username, Server), 'red'))
else:
    pg_log("eek -> ", con.lastErr, con.lastErrCode)
    sys.exit(1)

pg_log(colorize("Requesting Roster Info" , 'red'))
con.requestRoster()
con.sendInitPresence()
pg_log(colorize("Ok, ready" , 'red'))
pg_log(colorize("Type /help for help", 'red'))

JID = Username + '@' + Server + '/' + Resource

# jabber -> pgui setup

def idle(ev, win):
    inputs, outputs, errors = select([sys.stdin], [], [],1)

    if sys.stdin in inputs:
        doCmd(con,sys.stdin.readline())
    else:
        con.process(1)
app.link(idle, None, "idle")

def pg_send(ev, wid):
    txt = app.server.getstring(wid.text)[:-1]
    wid.text = ''
    if Who:
        doSend(con, txt)
    else:
        doCmd(con, txt)
app.link(pg_send, entry, 'activate')

apptitle = app.panelbar_label
if type(apptitle) is type(1L):
    # temporary workaround till library can know about property types
    apptitle = PicoGUI.Widget(app.server, apptitle, app)
apptitle.text = 'Jabber client: %s' % JID

# now run the app
def closeapp(ev, win):
    con.disconnect()
    pg_log(colorize("Bye!",'red'))
    sys.exit(0)
app.link(closeapp, app, "close")
app.server.focus(entry)
app.run()

