#!/usr/bin/env python2  
# You may need to change the above line to point at
# python rather than python2 depending on your os/distro
import Jabber, XMLStream
import socket
from select import select
from string import split,strip
import sys

True = 1
False = 0

# Change this to 0 if you dont want a color xterm
USE_COLOR = 1

Who = ''

def usage():
    print "%s: a simple python jabber client " % sys.argv[0]
    print "usage:"
    print "%s <server> - connect to <server> and register" % sys.argv[0]
    print "%s server> <username> <password> <resource>"    % sys.argv[0]
    print "            - connect to server and login   "
    sys.exit(0)

def doCmd(con,txt):
    global Who
    if txt[0] == '/' :
        cmd = split(txt)
        if cmd[0] == '/select':
            Who = cmd[1]
            print "%s selected" % cmd[1]
        elif cmd[0] == '/presence':
            to = cmd[1]
            type = cmd[2]
            con.send(Jabber.Presence(to, type))
        elif cmd[0] == '/subscribe':
            to = cmd[1]
            con.send(Jabber.Presence(to, 'subscribe'))
        elif cmd[0] == '/unsubscribe':
            to = cmd[1]
            con.send(Jabber.Presence(to, 'unsubscribe'))
        elif cmd[0] == '/roster':
            con.requestRoster()
            _roster = con.getRoster()
            for jid in _roster.getJIDs():
                print colorize("%s :: %s (%s/%s)" 
                               % ( jid, _roster.getOnline(jid),
                                   _roster.getStatus(jid),
                                   _roster.getShow(jid),
                                   ) , 'blue' )

        elif cmd[0] == '/agents':
            print con.requestAgents()
        elif cmd[0] == '/register':
            agent = ''
            if len(cmd) > 1:
                agent = cmd[1]
            con.requestRegInfo(agent)
            print con.getRegInfo()
        elif cmd[0] == '/exit':
            con.disconnect()
            print colorize("Bye!",'red')
            sys.exit(0)
        elif cmd[0] == '/help':
            print "commands are:"
            print "   /select <jabberid>"
            print "      - selects who to send messages to"
            print "   /subscribe <jid>"
            print "      - subscribe to jid's presence"
            print "   /unsubscribe <jid>"
            print "      - unsubscribe to jid's presence"
            print "   /presence <jabberid> <type>"
            print "      - sends a presence of <type> type to the jabber id"
            print "   /roster"
            print "      - requests roster from the server and "
            print "        display a basic dump of it."
            print "   /exit"
            print "      - exit cleanly"
        else:
            print colorize("uh?", 'red')
    else:
        if Who != '':
            msg = Jabber.Message(Who, strip(txt))
            msg.setType('chat')
            print "<%s> %s" % (JID, msg.getBody())
            con.send(msg)
        else:
            print colorize('Nobody selected','red')
            

def messageCB(con, msg):
    """Called when a message is recieved"""
    if msg.getBody(): ## Dont show blank messages ##
        print colorize('<' + str(msg.getFrom()) + '>', 'green') + ' ' + msg.getBody()

def presenceCB(con, prs):
    """Called when a presence is recieved"""
    who = str(prs.getFrom())
    type = prs.getType()
    if type == None: type = 'available'

    # subscription request: 
    # - accept their subscription
    # - send request for subscription to their presence
    if type == 'subscribe':
        print colorize("subscribe request from %s" % (who), 'blue')
        con.send(Jabber.Presence(to=who, type='subscribed'))
        con.send(Jabber.Presence(to=who, type='subscribe'))

    # unsubscription request: 
    # - accept their unsubscription
    # - send request for unsubscription to their presence
    elif type == 'unsubscribe':
        print colorize("unsubscribe request from %s" % (who), 'blue')
        con.send(Jabber.Presence(to=who, type='unsubscribed'))
        con.send(Jabber.Presence(to=who, type='unsubscribe'))

    elif type == 'subscribed':
        print colorize("we are now subscribed to %s" % (who), 'blue')

    elif type == 'unsubscribed':
        print colorize("we are now unsubscribed to %s"  % (who), 'blue')

    elif type == 'available':
        print colorize("%s is available (%s / %s)" % (who, prs.getShow(), prs.getStatus()),
                       'blue')
    elif type == 'unavailable':
        print colorize("%s is unavailable (%s / %s)" % (who, prs.getShow(), prs.getStatus()),
                       'blue')


def iqCB(con,iq):
    """Called when an iq is recieved, we just let the library handle it at the moment"""
    pass

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
Server = sys.argv[1]
Username = ''
Password = ''
Resource = 'default'


con = Jabber.Connection(host=Server,debug=False ,log=False) #log=sys.stderr)
try:
    con.connect()
except XMLStream.error, e:
    print "Couldn't connect: %s" % e
    sys.exit(0)
else:
    print colorize("Connected",'red')

con.setMessageHandler(messageCB)
con.setPresenceHandler(presenceCB)
con.setIqHandler(iqCB)

if len(sys.argv) == 2:
    # Set up a jabber account
    con.requestRegInfo()
    req = con.getRegInfo()
    print req[u'instructions']
    for info in req.keys():
        if info != u'instructions' and \
           info != u'key':
            print "enter %s;" % info
            con.setRegInfo( info,strip(sys.stdin.readline()) )
    con.sendRegInfo()
    req = con.getRegInfo()
    Username = req['username']
    Password = req['password']
else:
    Username = sys.argv[2]
    Password = sys.argv[3]
    Resource = sys.argv[4]

print colorize("Attempting to log in...", 'red')


if con.auth(Username,Password,Resource):
    print colorize("Logged in as %s to server %s" % ( Username, Server), 'red')
else:
    print "eek -> ", con.lastErr, con.lastErrCode
    sys.exit(1)

print colorize("Requesting Roster Info" , 'red')
con.requestRoster()
con.sendInitPresence()
print colorize("Ok, ready" , 'red')
print colorize("Type /help for help", 'red')

JID = Username + '@' + Server + '/' + Resource

while(1):
    inputs, outputs, errors = select([sys.stdin], [], [],1)

    if sys.stdin in inputs:
        doCmd(con,sys.stdin.readline())
    else:
        con.process(1)
    
        









