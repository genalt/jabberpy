#!/usr/bin/env python2  
import Jabber, XMLStream
import socket
from select import select
from string import split,strip
import sys

True = 1
False = 0

Who = ''

def usage():
    print "%s: a simple python jabber clinet " % sys.argv[0]
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
        elif cmd[0] == '/roster':
            con.requestRoster()
            print "ROSTER IS ",con.getRoster()
        elif cmd[0] == '/agents':
            print con.requestAgents()
        elif cmd[0] == '/register':
            agent = ''
            if len(cmd) > 1:
                agent = cmd[1]
            con.requestRegInfo(agent)
            print con.getRegInfo()


        elif cmd[0] == '/help':
            print "commands are:"
            print "   /select <jabberid>"
            print "      - selects who to send messages to"
            print "   /presence <jabberid> <type>"
            print "      - sends a presence to the jabber id"
            print "        where type one of subscribe, subscribed"
            print "        unsubscribe, unsubscribed "
            print "   /roster"
            print "      - requests roster from the server and "
            print "        display a basic dump of it."
            print ""
    else:
        if Who != '':
            con.send(Jabber.Message(Who, strip(txt)))
        else:
            print "Nobody selected"
            

def messageCB(con, msg):
    print " %s -> %s " % (msg.getFrom(), msg.getBody())
def presenceCB(con, prs):
    print "got presence from %s - %s" % (prs.getFrom(), prs.getStatus())
def iqCB(con,iq):
    ##print "got iq type - %s" % iq.getType() 
    pass

if len(sys.argv) == 1: usage()
Server = sys.argv[1]
Username = ''
Password = ''
Resource = 'default'


con = Jabber.Connection(host=Server,debug=False)
try:
    con.connect()
except XMLStream.error, e:
    print "Couldn't connect: %s" % e 
    sys.exit(0)
else:
    print "Connected"

con.setMessageHandler(messageCB)
con.setPresenceHandler(presenceCB)
con.setIqHandler(iqCB)

if len(sys.argv) == 2:
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
    ## TODO , should really disconect now, and reconnect !
else:
    Username = sys.argv[2]
    Password = sys.argv[3]
    Resource = sys.argv[4]

print "Attempting to log in..."

## should be try around this ?
if con.auth(Username,Password,Resource):
    print "Logged in as %s to server %s" % ( Username, Server )
    print "Type /help for help"
else:
    print "eek -> ", con.lastErr, con.lastErrCode
    sys.exit(1)

con.sendInitPresence()

while(1):
    inputs, outputs, errors = select([sys.stdin], [], [],0)
    #inputs.extend(errors)

    if sys.stdin in inputs:
        doCmd(con,sys.stdin.readline())
    else:
        con.process(10)
    
        






