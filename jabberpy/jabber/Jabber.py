import XMLStream
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
        
        self.lastErr = ''
        self.lastErrCode = 0

        XMLStream.Client.__init__(self, host, port, 'jabber:client', debug, log)

    def getAnID(self):
        self._id = self._id + 1
        return self._id
    

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
            for n in root_node.kids:
                if n.name == 'query':
                    ## Build roster ###
                    if n.namespace == 'jabber:iq:roster' \
                       and root_node.attrs['type'] == 'result':
                        self._roster = {}
                        for item in n.kids:
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
                        
                    elif n.namespace == 'jabber:iq:register':
                        if root_node.attrs['type'] == 'result':
                            self._reg_info = {}
                            for item in n.kids:
                                data = None
                                if item.data: data = item.data
                                self._reg_info[item.name] = data
                        else:
                            self.DEBUG("print type is %s" % root_node.attrs['type'])

                    elif n.namespace == 'jabber:iq:agents':
                        if root_node.attrs['type'] == 'result':
                            self.DEBUG("got agents result")
                            self._agents = {}
                            for agent in n.kids:
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

    
    def auth(self,username,passwd,resource):
        str =  u"<iq type='set'>                    \
                <query xmlns='jabber:iq:auth'><username>%s</username><password>%s</password> \
                <resource>%s</resource></query></iq>" % ( username,passwd,resource )
        self.send(str)
        if (find(self.read(),'error') == -1):         ## this will fire off a callback for ok ? 
            return True
        else:
            return False

    def requestRoster(self):
        self.send(u"<iq type='get'><query xmlns='jabber:iq:roster'/></iq>")
        self._roster = {}
        while (not self._roster): self.process(0)
        
    def requestRegInfo(self,agent=''):
        if agent: agent = agent + '.'
        self.send(u"<iq type='get' to='%s%s'><query xmlns='jabber:iq:register'/></iq>" % ( agent ,self._host ))
        while (not self._reg_info): self.process(0)
        
    def send(self, what):
         self.DEBUG("type is %s " % type(what))
         if type(what) is type("") or type(what) is type(u""): ## Is it a string ?
             XMLStream.Client.write(self,what)
         else:       ## better add if isinstance(what, protocol_superclass) ..?
             XMLStream.Client.write(self,what.__str__())

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
        str =u'<iq type="set" to="' + agent + self._host + '"> \
               <query xmlns="jabber:iq:register">'
        for info in self._reg_info.keys():
            str = str + u"<%s>%s</%s>" % ( info, self._reg_info[info], info )
        str = str + u"</query></iq>"
        self.send(str)

    def requestAgents(self):
        agents_iq = Iq(type='get')
        agents_iq.setQueryNS('jabber:iq:agents')
        self.send(agents_iq)
        self._agents = {}
        while (not self._agents): self.process(0)
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
        q= self._node.getTag('query')
        if q:
            q.namespace = namespace
        else:
            self._node.insertTag('query').setNamespace(namespace)

    def getQueryNode(self):
        try: return self._node.getTag('query')
        except: return None












