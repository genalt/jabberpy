import XMLStream
import sha
from string import split,find,replace

False = 0;
True  = 1;

def getAnID():
    ## need to figure out how to set static data ?
    pass

class Connection(XMLStream.Client):
    def __init__(self, host, port=5222, debug=True, log=False):
        self.msg_hdlr  = None
        self.pres_hdlr = None
        self.iq_hdlr   = None

        self._roster = {}
        self._agents = {}
        self._reg_info = {}
        self._reg_agent = ''

        self._id = 0;
        self._expected = {}
        
        self.lastErr = ''
        self.lastErrCode = 0

        XMLStream.Client.__init__(self, host, port, 'jabber:client', debug, log)

    def getAnID(self):
        self._id = self._id + 1
        return str(self._id)
    

    def dispatch(self, root_node ):
        self.DEBUG("dispatch called")
        
        if root_node.name == 'message':
            self.DEBUG("got message dispatch")
            
            msg_obj = Message(node=root_node)
            self.messageHandler(msg_obj)
            
        elif root_node.name == 'presence':
            self.DEBUG("got presence dispatch")

            pres_obj = Presence(node=root_node)
            self.presenceHandler(pres_obj)

            
        elif root_node.name == 'iq':
            ## Check for an error
            self.DEBUG("got an iq");
            iq_obj = Iq(node=root_node)
            
            if root_node.attrs['type'] == 'error':
                for n in root_node.kids:
                    if n.name == 'error':
                        self.lastErr = n.data
                        self.lastErrCode = n.attrs['code']


            #
            # TODO: change all below code to use node methods
            #
            queryNS = iq_obj.getQuery()
            if queryNS and root_node.attrs['type'] == 'result':
                    ## Build roster ###
                if queryNS == 'jabber:iq:roster': 
                    self._roster = {}
                    for item in iq_obj.getQueryNode().kids:
                        jid = None
                        name = None
                        sub = None
                        ask = None
                        if item.attrs.has_key('jid'):
                            jid = item.attrs['jid']
                        if item.attrs.has_key('name'):
                            name = item.attrs['name']
                        if item.attrs.has_key('subscription'):
                            sub = item.attrs['subscription']
                        if item.attrs.has_key('ask'):
                            ask = item.attrs['ask']
                        if jid:
                            self._roster[jid] = \
                            { 'name': name, 'ask': ask, 'subscription': sub }
                        else:
                            self.DEBUG("roster - jid not defined ?")
                    self.DEBUG("roster => %s" % self._roster)
                        
                elif queryNS == 'jabber:iq:register':
                        self._reg_info = {}
                        for item in iq_obj.getQueryNode().kids:
                            data = None
                            if item.data: data = item.data
                            self._reg_info[item.name] = data
                    
                elif queryNS == 'jabber:iq:agents':
                        self.DEBUG("got agents result")
                        self._agents = {}
                        for agent in iq_obj.getQueryNode().kids:
                            if agent.name == 'agent': ## hmmm
                                self._agents[agent.attrs['jid']] = {}
                                for info in agent.kids:
                                    data = None
                                    if info.data: data = info.data
                                self._agents[agent.attrs['jid']][info.name] = data
                else:
                    pass
                    
            self.iqHandler(iq_obj)
            
        else:
            self.DEBUG("whats a tag -> " + root_node.name)

        if root_node.getAttr('id'):
            self._expected[root_node.getAttr('id')] = root_node
            


    def waitForResponse(self, ID):
        while not self._expected.has_key(ID):
            print "waiting on %s" % str(ID)
            self.process(0)
        response = self._expected[ID]
        del self._expected[ID]
        return response ## needed ?

    def auth(self,username,passwd,resource):
        auth_get_iq = Iq(type='get')
        auth_get_iq.setID('auth-get')
        q = auth_get_iq.setQuery('jabber:iq:auth')
        q.insertTag('username').insertData(username)
        self.send(auth_get_iq)
        auth_ret_node = self.waitForResponse("auth-get")
        self.DEBUG("auth-get node arrived!")

        for child in auth_ret_node.getTag('query').getChildren():
            self.DEBUG("---> %s" % ( child.getName() ) )

        auth_set_iq = Iq(type='set')
        auth_set_iq.setID('auth-set')
        q = auth_set_iq.setQuery('jabber:iq:auth')
        q.insertTag('username').insertData(username)
        q.insertTag('resource').insertData(resource)

        if auth_ret_node.getTag('query').getTag('digest'):
            self.DEBUG("digest authentication supported")
            digest = q.insertTag('digest')
            digest.insertData(sha.new(
                self.getStreamID() + passwd).hexdigest()
                              )
        else:
            q.insertTag('password').insertData(passwd)
        self.DEBUG("sending %s" % ( str ) )

        # back on track
        self.send(auth_set_iq) ## TODO: improve for wait !!


        ## TODO: imporve !!!!!!!!!
        if (find(self.read(),'error') == -1):     
            return True
        else:
            return False


##        str =  u"<iq type='set'>                    \
##                <query xmlns='jabber:iq:auth'><username>%s</username><password>%s</password> \
##                <resource>%s</resource></query></iq>" % ( username,passwd,resource )
##        self.send(str)
##        if (find(self.read(),'error') == -1):         ## this will fire off a callback for ok ? 
##            return True
##        else:
##            return False
##

    def requestRoster(self):
        id = self.getAnID()
        rost_iq = Iq(type='get')
        rost_iq.setQuery('jabber:iq:roster')
        rost_iq.setID(id)
        self.send(rost_iq)
        self._roster = {}
        self.waitForResponse(id)
        self.DEBUG("got roster response")
        self.DEBUG("roster -> %s" % str(self._agents))
        return self._roster
        
    def requestRegInfo(self,agent=''):
        if agent: agent = agent + '.'
        id = self.getAnID()
        reg_iq = Iq(type='get', to = agent + self._host)
        reg_iq.setQuery('jabber:iq:register')
        reg_iq.setID(id)
        self.send(reg_iq)
        self._reg_info = {}
        self.waitForResponse(id)
        self.DEBUG("got reg response")
        self.DEBUG("roster -> %s" % str(self._agents))
        
    def send(self, what):
         XMLStream.Client.write(self,str(what))
##         if type(what) is type("") or type(what) is type(u""): ## Is it a string ?
##             XMLStream.Client.write(self,what)
##         else:       ## better add if isinstance(what, protocol_superclass) ..?
##             XMLStream.Client.write(self,str(what))
##
    def sendInitPresence(self):
        self.send("<presence/>");

    def setMessageHandler(self, func):
        self.msg_hdlr = func

    def setPresenceHandler(self, func):
        self.pres_hdlr = func

    def setIqHandler(self, func):
        self.iq_hdlr = func

    def getRoster(self):
        return self._roster
        # send request
        # do read
        # return internal roster hash

    def getRegInfo(self):
        return self._reg_info

    def setRegInfo(self,key,val):
        self._reg_info[key] = val

    def sendRegInfo(self, agent=''):
        if agent: agent = agent + '.'
        iq_reg = Iq(to = agent + self._host, type='set')
        q = iq_reg.setQuery('jabber:iq:register')
        print q
        for info in self._reg_info.keys():
            q.insertTag(info).putData(self._reg_info[info])
        self.send(iq_reg)
        ## TODO: wait on an ID here

    def requestAgents(self):
        id = self.getAnID()
        agents_iq = Iq(type='get')
        agents_iq.setQuery('jabber:iq:agents')
        agents_iq.setID(id)
        self.send(agents_iq)
        self._agents = {}
        self.waitForResponse(id)
        self.DEBUG("got agents response")
        self.DEBUG("agents -> %s" % str(self._agents))
        return self._agents

    def messageHandler(self, msg_obj): ## Overide If You Want ##
        if self.msg_hdlr != None: self.msg_hdlr(self, msg_obj)
        
    def presenceHandler(self, pres_obj): ## Overide If You Want ##
        if self.pres_hdlr != None: self.pres_hdlr(self, pres_obj)

    def iqHandler(self, iq_obj): ## Overide If You Want ##
        if self.iq_hdlr != None: self.iq_hdlr(self, iq_obj)


#
# TODO:
# all the below structures should really just define there 'top level' tag.
# Tags inside this should really be an XMLStream Node as a .kids attr ?
# 
# The Iq object currently does this. Need to think more obout it
#

class Protocol:
    def __init__(self):
        self._node = None

    def asNode(self):
        return self._node
    
    def __str__(self):
        return self._node.__str__()

    def getTo(self):
        try: return self._node.getAttr('to')
        except: return None
        
    def getFrom(self):
        try: return self._node.getAttr('from')
        except: return None

    def getType(self):
        try: return self._node.getAttr('type')
        except: return None

    def getID(self):
        try: return self._node.getAttr('id')
        except: return None

    def setTo(self,val): self._node.putAttr('to', val)

    def setFrom(self,val): self._node.putAttr('from', val)

    def setType(self,val): self._node.putAttr('type', val)

    def setID(self,val): self._node.putAttr('id', val)


class Message(Protocol):
    def __init__(self, to='', body='', node=None):
        ##self.frm = 'mallum@jabber.com'
        if node:
            self._node = node
        else:
            self._node = XMLStream.XMLStreamNode(tag='message')
        if to: self.setTo(to)
        if body: self.setBody(body)
        
    def getBody(self):
        body = self._node.getTag('body')
        try: return self._node.getTag('body').data
        except: return None

    def getType(self):
        try: return self._node.getAttr('type')
        except: return None

    def getSubject(self): 
        try: return self._node.getTag('subject').data
        except: return None

    def getThread(self):
        try: return self._node.getTag('thread').data
        except: return None
        
    def getError(self):
        pass
    def getErrorCode(self):
        pass
    def getTimestamp(self):
        pass

    def setBody(self,val):
        body = self._node.getTag('body')
        if body:
            body.putData(val)
        else:
            body = self._node.insertTag('body').putData(val)
            
    def setSubject(self,val):
        subj = self._node.getTag('subject')
        if subj:
            subj.putData(val)
        else:
            self._node.insertTag('subject').putData(val)

    def setThread(self,val): pass
    def setError(self,val): pass
    def setErrorCode(self,val): pass
    def setTimestamp(self,val): pass

    
    def build_reply(self, reply_txt=''):
        return Message(to=self.getFrom(), body=reply_txt)



class Presence(Protocol):
    def __init__(self, to=None, type=None, node=None):
        ##self.frm = 'mallum@jabber.com'
        if node:
            self._node = node
        else:
            self._node = XMLStream.XMLStreamNode(tag='presence')
        if to: self.setTo(to)
        if type: self.setType(type)


    def getStatus(self):
        try: return self._node.getTag('status').getData()
        except: return None

    def getShow(self):
        try: return self._node.getTag('show').getData()
        except: return None

    def getPriority(self):
        try: return self._node.getTag('priority').getData()
        except: return None
    
    def setShow(self,val):
        show = self._node.getTag('show')
        if show:
            show.putData(val)
        else:
            self._node.insertTag('show').putData(val)

    def setStatus(self,val):
        status = self._node.getTag('status')
        if status:
            status.putData(val)
        else:
            self._node.insertTag('status').putData(val)

    def setPriority(self,val):
        pri = self._node.getTag('priority')
        if pri:
            pri.putData(val)
        else:
            self._node.insertTag('priority').putData(val)


class Iq(Protocol): 
    def __init__(self, to='', type=None, node=None):
        if node:
            self._node = node
        else:
            self._node = XMLStream.XMLStreamNode(tag='iq')
        if to: self.setTo(to)
        if type: self.setType(type)
        

    def getQuery(self):
        "returns the query namespace"
        try: return self._node.getTag('query').namespace
        except: return None

    def setQuery(self,namespace):   
        q = self._node.getTag('query')
        if q:
            q.namespace = namespace
        else:
            q = self._node.insertTag('query')
            q.setNamespace(namespace)
        return q
        
    def getQueryNode(self):
        try: return self._node.getTag('query')
        except: return None

    def setQueryNode(self):
        q = self._node.getTag('query')
        if q:
            q.putData(val)
        else:
            self._node.insertTag('query').putData(val)












