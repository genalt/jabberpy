## Stick this in the <browse/> element of your jabber.xml
## <service jid="mailcheck" name="IMAP Mail Checker">
##   <ns>jabber:iq:register</ns>
##   <ns>jabber:iq:gateway</ns>
## </service>
##
## Stick this in with the other <service/> elements
## <service id="mailcheck">
##     <accept>
##         <ip/>
##         <secret>secret</secret>
##         <port>6969</port>
##     </accept>
## </service>


import jabber
import sys
import sha
import imaplib
import pickle
import string

# mailchecker client
class MCClient:
    jid = None
    username = None
    password = None
    hostname = None
    directory = None
    folders = []
    online = 0
    status = None
    imap = None

    def __init__(self, jid, username, password, hostname, directory, folders):
        self.jid = jid
        self.username = username
        self.password = password
        self.hostname = hostname
        self.directory = directory
        self.folders = string.split(folders, ':')

    def doit(self, con):
        """query the mail server for new messages"""
        pass

    def cleanup(self):
        """Close down IMAP connection and perform any other necessary cleanup"""
        pass

    def setStatus(self, status):
        """Set the client's "verbose" status"""
        self.status = status

    def setShow(self, show):
        """Set the client's show mode; one of away, chat, xa, dnd, or 'None'"""
        # http://docs.jabber.org/jpg/html/main.html#REFSHOW
        # One of away, chat, xa, or dnd.
        self.show = show
        self.setOnline(1)

    def setOnline(self, online):
        """Set whether the user is online or not"""
        self.online = online

    def isOnline(self):
        """Return the state of the user's online'ness"""
        return(self.online)

    def isAvailable(self):
        """Return a boolean based on the user's show status"""
        
        # return false if xa, dnd or away (?)
        if (self.show == None) or (self.show == 'chat'):
            return(1)
        else:
            return(0)
    
# dict of keys
keys = {}

def iqCB(con, iq):
    print "Iq:", str(iq)
    resultIq = jabber.Iq(to=iq.getFrom())
    resultIq.setID(iq.getID())
    resultIq.setFrom(iq.getTo())

    query_result = resultIq.setQuery(iq.getQuery())

    type = iq.getType()
    query_ns = iq.getQuery()

    # switch on type: get, set, result error
    # switch on namespaces

    if query_ns == jabber.NS_REGISTER:
        if type == 'get':
            resultIq.setType('result')

            # generate a key to be passed to the user; it will be checked
            # later.  yes, we're storing a sha object
            iq_from = str(iq.getFrom())
            keys[iq_from] = sha.new(iq_from)

            # tell the client the fields we want
            fields = {
                'username': None,
                'password': None,
                'instructions': 'Enter your username, password, IMAP hostname, directory, and :-separated list of folders to check',
                'key': keys[iq_from].hexdigest(),
                'hostname': None,
                'directory': None,
                'folders': 'INBOX'
                }

            for field in fields.keys():
                field_node = query_result.insertTag(field)
                if fields[field]:
                    field_node.putData(fields[field])

            con.send(resultIq)

        elif type == 'set':
            # before anything else, verify the key
            client_key_node = iq.getQueryNode().getTag('key')
            if not client_key_node:
                resultIq.setType('error')
                resultIq.setError('no key given!')
                con.send(resultIq)
            else:
                # verify key
                if keys[str(iq.getFrom())].hexdigest() == client_key_node.getData():
                    # key is good
                    if iq.getQueryNode().getTag('remove'):
                        # user is trying to unregister
                        # TODO. :-)
                        del clients[iq.getFrom().getStripped()]
                    else:
                        # someone is trying to register
                        jid = iq.getFrom().getStripped()
                        username = iq.getQueryNode().getTag('username')
                        if username:
                            username = str(username.getData())

                        password = iq.getQueryNode().getTag('password')
                        if password:
                            password = str(password.getData())
                        
                        hostname = iq.getQueryNode().getTag('hostname')
                        if hostname:
                            hostname = str(hostname.getData())
                        
                        directory = iq.getQueryNode().getTag('directory')
                        if directory:
                            directory = str(directory.getData())
                        
                        folders = iq.getQueryNode().getTag('folders')
                        if folders:
                            folders = str(folders.getData())
                        
                        
                        client = MCClient(jid, username, password, hostname, directory, folders)

                        clients[client.jid] = client

                        # subscribe to the client's presence
                        sub_req = jabber.Presence(iq.getFrom(), type='subscribe')
                        sub_req.setFrom(str(iq.getTo()) + "/registered")
                        con.send(sub_req)

                        resultIq.setType('result')
                        con.send(resultIq)
                else:
                    resultIq.setType('error')
                    resultIq.setError('invalid key', 400)
                    con.send(resultIq)

                # done with key; delete it
                del keys[str(iq.getFrom())]
        else:
            print "don't know how to handle type", type, "for query", query_ns
            
    elif (query_ns == jabber.NS_AGENT) and (type == 'get'):
        # someone wants information about us
        resultIq.setType('result')

        responses = {
            'name': "Mailchecker",
            # 'url': None,
            'description': "This is the mailchecker component",
            'transport': "don't know what should go here...",
            'register': None, # we can be registered with
            'service': 'test' # nothing really standardized here...
            }

        for response in responses.keys():
            resp_node = query_result.insertTag(response)
            if responses[response]:
                resp_node.putData(responses[response])

        con.send(resultIq)

    else:
        print "don't know how to handle type", type, "for query", query_ns

def presenceCB(con, pres):
    print "Presence:", str(pres)

    # presence reply to use later on
    p = jabber.Presence(to=pres.getFrom())
    p.setFrom(pres.getTo())
    
    type = pres.getType()

    # find the client object
    if str(pres.getFrom().getStripped()) in clients.keys():
        client = clients[pres.getFrom().getStripped()]
    else:
        print("not able to find client for " + pres.getFrom().getStripped())
        
        client = None
        if type != 'unsubscribed':
            type = 'unsubscribe'
            
    if not type:
        type = 'available'

    print(pres.getFrom().getStripped() + " is " + type)

    if type == 'unavailable':
        # user went offline
        client.setOnline(0)

        p.setType('unavailable')
        con.send(p)
        
    elif type == 'subscribe':
        # user wants to subscribe to our presence; oblige, and ask for his
        p.setType('subscribed')
        con.send(p)

        p.setType('subscribe')
        con.send(p)

    elif type == 'unsubscribe':
        p.setType('unsubscribed')
        con.send(p)

        p.setType('unsubscribe')
        con.send(p)
        
    elif type == 'unsubscribed':
        # now unsubscribe from the user's presence
        pass

    elif type == 'probe':
        # send our presence
        p.setType('available')
        con.send(p)
        
    elif type == 'available':
        # user is online
        client.setStatus(pres.getStatus())
        client.setShow(pres.getShow())

        p.setType('available')
        con.send(p)

con = jabber.Component(host='webtechtunes.hq.insight.com', debug=0, port=6969, log='log')

try:
    clients = pickle.load(open('clients.p'))
except IOError, e:
    print(e)
    clients = {}
    
try:
    con.connect()
except IOError, e:
    print "Couldn't connect: %s" % e
    sys.exit(0)
else:
    print "Connected"
    
con.process(1)

if con.auth('secret'):
    print "connected"
else:
    print "problems with handshake: ", con.lastErr, con.lastErrCode
    sys.exit(1)

# con.registerHandler('message',messageCB)
con.registerHandler('presence',presenceCB)
con.registerHandler('iq',iqCB)

p = jabber.Presence(type='available')
p.setFrom('mailcheck/registered')
for c in clients.keys():
    p.setTo(clients[c].jid)
    con.send(p)

try:
    while(1):
        con.process(10)

        # whoo baby, is this a kludge.  Should really have a bona-fide event
        # loop or thread that processes the user's email checking, or at least
        # build up a timer type element that only runs this once every five
        # minutes or so...
        for c in clients.keys():
            clients[c].doit()
            
except KeyboardInterrupt:
    p = jabber.Presence(type='unavailable')
    p.setFrom('mailcheck/registered')
    for c in clients.keys():
        p.setTo(clients[c].jid)
        con.send(p)

    pickle.dump(clients, open('clients.p', 'w'))

    con.disconnect()
