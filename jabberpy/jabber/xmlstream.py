##   xmlstream.py 
##
##   Copyright (C) 2001 Matthew Allum
##
##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU Lesser General Public License as published
##   by the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU Lesser General Public License for more details.


"""\
xmlstream.py provides simple functionality for implementing
XML stream based network protocols. It is used as a  base
for jabber.py.

xmlstream.py manages the network connectivity and xml parsing
of the stream. When a complete 'protocol element' ( meaning a
complete child of the xmlstreams root ) is parsed the dipatch
method is called with a 'Node' instance of this structure.
The Node class is a very simple XML DOM like class for
manipulating XML documents or 'protocol elements' in this
case.

"""

# $Id$

import site
site.encoding = 'UTF-8'
import time, sys, re, socket
from select import select
from string import split,find,replace,join
import xml.parsers.expat
import debug
_debug=debug

VERSION = "0.4+"

False = 0
True  = 1

TCP     = 1
STDIO   = 0
TCP_SSL = 2

ENCODING = site.encoding 

BLOCK_SIZE  = 1024     ## Number of bytes to get at at time via socket
                       ## transactions

DBG_INIT, DBG_ALWAYS = debug.DBG_INIT, debug.DBG_ALWAYS
DBG_CONN_ERROR = 'conn-error'    ; debug.debug_flags.append( DBG_CONN_ERROR )
DBG_XML_PARSE = 'xml-parse'      ; debug.debug_flags.append( DBG_XML_PARSE )
DBG_XML_RAW = 'xml-raw'          ; debug.debug_flags.append( DBG_XML_RAW )
DBG_XML = [ DBG_XML_PARSE, DBG_XML_RAW ] # sample multiflag


def XMLescape(txt):
    "Escape XML entities"
    txt = replace(txt, "&", "&amp;")
    txt = replace(txt, "<", "&lt;")
    txt = replace(txt, ">", "&gt;")
    return txt

def XMLunescape(txt):
    "Unescape XML entities"
    txt = replace(txt, "&gt;", ">")
    txt = replace(txt, "&lt;", "<")
    txt = replace(txt, "&amp;", "&")
    return txt

class error:
    def __init__(self, value):
        self.value = str(value)
    def __str__(self):
        return self.value
    
class Node:
    """A simple XML DOM like class"""
    def __init__(self, tag=None, parent=None, attrs=None, payload=None, node=None):
        if node:
            if type(node)<>type(self): node=NodeBuilder(node).getDom()
            self.name,self.namespace,self.attrs,self.data,self.kids,self.parent = \
                node.name,node.namespace,node.attrs,node.data,node.kids,node.parent
        else:
            self.name,self.namespace,self.attrs,self.data,self.kids,self.parent = 'tag','',{},[],[],None

        if tag: self.namespace, self.name = (['']+tag.split())[-2:]

        if parent: self.parent = parent

#        if self.parent and not self.namespace: self.namespace=self.parent.namespace	# Doesn't checked if this neccessary

        if attrs: self.attrs = attrs

        if payload:
            if type(payload) not in (type([]),type(1,)): payload=[payload]
            for i in payload:
                if type(i)==type(self): self.insertNode(i)
                else: self.insertXML(i)
#                self.insertNode(Node(node=i))	# Alternative way. Needs perfomance testing.

    def setParent(self, node):
        "Set the nodes parent node."
        self.parent = node

    def getParent(self):
        "return the nodes parent node."
        return self.parent

    def getName(self):
        "Set the nodes tag name."
        return self.name

    def setName(self,val):
        "Set the nodes tag name."
        self.name = val

    def putAttr(self, key, val):
        "Add a name/value attribute to the node."
        self.attrs[key] = val

    def getAttr(self, key):
        "Get a value for the nodes named attribute."
        try: return self.attrs[key]
        except: return None
        
    def putData(self, data):
        "Set the nodes textual data" 
        self.data.append(data)

    def insertData(self, data):
        "Set the nodes textual data" 
        self.data.append(data)

    def getData(self):
        "Return the nodes textual data" 
        return join(self.data, '')

    def getDataAsParts(self):
        "Return the node data as an array" 
        return self.data

    def getNamespace(self):
        "Returns the nodes namespace." 
        return self.namespace

    def setNamespace(self, namespace):
        "Set the nodes namespace." 
        self.namespace = namespace

    def insertTag(self, name):
        """ Add a child tag of name 'name' to the node.

            Returns the newly created node.
        """
        newnode = Node(tag=name, parent=self)
        self.kids.append(newnode)
        return newnode

    def insertNode(self, node):
        "Add a child node to the node"
        self.kids.append(node)
        return node

    def insertXML(self, xml_str):
        "Add raw xml as a child of the node"
        newnode = NodeBuilder(xml_str).getDom()
        self.kids.append(newnode)
        return newnode

    def __str__(self):
        return self._xmlnode2str()

    def _xmlnode2str(self, parent=None):
        """Returns an xml ( string ) representation of the node
         and it children"""
        s = "<" + self.name  
        if self.namespace:
            if parent and parent.namespace != self.namespace:
                s = s + " xmlns = '%s' " % self.namespace
        for key in self.attrs.keys():
            val = str(self.attrs[key])
            s = s + " %s='%s'" % ( key, XMLescape(val) )
        s = s + ">"
        cnt = 0 
        if self.kids != None:
            for a in self.kids:
                if (len(self.data)-1) >= cnt: s = s + XMLescape(self.data[cnt])
                s = s + a._xmlnode2str(parent=self)
                cnt=cnt+1
        if (len(self.data)-1) >= cnt: s = s + XMLescape(self.data[cnt])
        s = s + "</" + self.name + ">"
        return s

    def getTag(self, name):
        """Returns a child node with tag name. Returns None
        if not found."""
        for node in self.kids:
            if node.getName() == name:
               return node
        return None

    def getTags(self, name):
        """Like getTag but returns a list with matching child nodes"""
        nodes=[]
        for node in self.kids:
            if node.getName() == name:
               nodes.append(node)
        return nodes
        

    def getChildren(self):
        """Returns a nodes children"""
        return self.kids

class NodeBuilder:
    """builds a 'minidom' from data parsed to it. Primarily for insertXML
       method of Node"""
    def __init__(self,data=None):
        self._parser = xml.parsers.expat.ParserCreate(namespace_separator=' ')
        self._parser.StartElementHandler  = self.unknown_starttag
        self._parser.EndElementHandler    = self.unknown_endtag
        self._parser.CharacterDataHandler = self.handle_data

        self.__depth = 0
        self._dispatch_depth = 1
        
        if data: self._parser.Parse(data,1)

    def unknown_starttag(self, tag, attrs):
        """XML Parser callback"""
        self.__depth = self.__depth + 1
        self.DEBUG("DEPTH -> %i , tag -> %s, attrs -> %s" % \
                   (self.__depth, tag, str(attrs)),DBG_XML_PARSE )
        if self.__depth == self._dispatch_depth:
            self._mini_dom = Node(tag=tag, attrs=attrs)
            self._ptr = self._mini_dom
        elif self.__depth > self._dispatch_depth:
            self._ptr.kids.append(Node(tag=tag,parent=self._ptr,attrs=attrs))
            self._ptr = self._ptr.kids[-1]
        else:                           ## it the stream tag:
            if attrs.has_key('id'):
                self._incomingID = attrs['id']

    def unknown_endtag(self, tag ):
        """XML Parser callback"""
        self.DEBUG("DEPTH -> %i" % self.__depth,DBG_XML_PARSE)
        if self.__depth == self._dispatch_depth:
            self.dispatch(self._mini_dom)
        elif self.__depth > self._dispatch_depth:
            self._ptr = self._ptr.parent
        else:
            self.DEBUG("*** Stream terminated ? ****",DBG_CONN_ERROR)
        self.__depth = self.__depth - 1

    def handle_data(self, data):
        """XML Parser callback"""
        self.DEBUG("data-> " + data,DBG_XML_PARSE)
        self._ptr.data.append(data)

    def dispatch(self,dom):
        pass

    def DEBUG(dup1,dup2=None):
        pass

    def getDom(self):
        return self._mini_dom


class Stream(NodeBuilder):
    def __init__(
                 self, host, port, namespace,
                 debug=[DBG_ALWAYS],
                 log=None,
                 sock=None,
                 id=None,
                 connection=TCP
                 ):

        NodeBuilder.__init__(self)

        self._host = host
        self._port = port 
        self._namespace = namespace
        self._sock = sock

        self._sslObj    = None
        self._sslIssuer = None
        self._sslServer = None

        self._incomingID = None
        self._outgoingID = id
        
        self._debug = _debug.Debug(debug)
        self.DEBUG = self._debug.show # makes it backwards compatible with current code
        self._connection=connection

        self.DEBUG("stream init called",DBG_INIT)

        if log:
            if type(log) is type(""):
                try:
                    self._logFH = open(log,'w')
                except:
                    print "ERROR: can open %s for writing"
                    sys.exit(0)
            else: ## assume its a stream type object
                self._logFH = log
        else:
            self._logFH = None
        self._timestampLog = True

    def timestampLog(self,timestamp):
        """ Enable or disable the showing of a timestamp in the log.
            By default, timestamping is enabled.
        """
        self._timestampLog = timestamp

    def getSocket(self):
        return self._sock

    def header(self):    
        pass

    ##def syntax_error(self, message):
    ##    self.DEBUG("error " + message,DBG_CONN_ERROR)

    def _do_read( self, action, buff_size ):
        """workhorse for read() method.

        added 021231 by jaclu"""
        data=''
        data_in = action(buff_size)
        while data_in:
            data = data + data_in
            if len(data_in) != buff_size and data[-buff_size:].rstrip()[-1]=='>':
                break
            data_in = action(buff_size)
        return data

    def read(self):
        """Reads incoming data. Called by process() so nonblocking

        changed 021231 by jaclu
        """
        if self._connection == TCP:
            raw_data = self._do_read(self._sock.recv, BLOCK_SIZE)
        elif self._connection == TCP_SSL:
            raw_data = self._do_read(self._sslObj.read, BLOCK_SIZE)
        elif self._connection == STDIO:
            raw_data = self._do_read(self.stdin.read, 1024)
        else:
            raw_data = '' # should never get here

        # just encode incoming data once!
        data = unicode(raw_data,'utf-8').encode(ENCODING,'replace')
        self.DEBUG("got data %s" % data,DBG_XML_RAW )
        self.log(data, 'RECV:')
        self._parser.Parse(data)
        return data

    def write(self,raw_data=u''):
        """Writes raw outgoing data. Blocks until done.
           If supplied data is not unicode string, xmlstream.ENCODING
           is used for convertion. Avoid this!
           Always send your data as a unicode string."""
        if type(raw_data) == type(''):
            data_out = unicode(raw_data,ENCODING)
        data_out = raw_data.encode('utf-8','replace')
        try:
            if self._connection == TCP:
                self._sock.send (data_out)
            elif self._connection == TCP_SSL:
                self._sslObj.write(data_out)
            elif self._connection == STDIO:
                self.stdout.write(data_out)
            else:
                pass
            self.log(data_out, 'SENT:')
            self.DEBUG("sent %s" % data_out,DBG_XML_RAW)
        except:
            self.DEBUG("xmlstream write threw error",DBG_CONN_ERROR)
            self.disconnected()
            
    def process(self,timeout):
        
        reader=Node

        if self._connection == TCP: 
            reader = self._sock
        elif self._connection == TCP_SSL:
            reader = self._sock
        elif self._connection == STDIO:
            reader = sys.stdin
        else:
            pass

        ready_for_read,ready_for_write,err = \
                        select( [reader],[],[],timeout)
        for s in ready_for_read:
            if s == reader:
                if not len(self.read()): # length of 0 means disconnect
                    self.disconnected()
                    return False
                return True
        return False

    def disconnect(self):
        """Close the stream and socket"""
        self.write ( "</stream:stream>" )
        self._sock.close()
        self._sock = None
        
    def disconnected(self): ## To be overidden ##
        """Called when a Network Error or disconnection occurs.
        Designed to be overidden"""
        self.DEBUG("Network Disconnection",DBG_CONN_ERROR)
        raise error("network error")

    def log(self, data, inout=''):
        """Logs data to the specified filehandle. Data is time stamped 
        and prefixed with inout"""
        if self._logFH is not None:
            if self._timestampLog:
                self._logFH.write("%s - %s - %s\n" % (time.asctime(), inout, data))
            else:
                self._logFH.write("%s - %s\n" % (inout, data ) )
            self._logFH.flush()

    def getIncomingID(self):
        """Returns the streams ID"""
        return self._incomingID

    def getOutgoingID(self):
        """Returns the streams ID"""
        return self._incomingID


class Client(Stream):

    def connect(self):
        """Attempt to connect to specified host"""

        self.DEBUG("client connect called to %s %s type %i" % (self._host,
                                                               self._port,
                                                               self._connection), DBG_INIT )

        ## TODO: check below that stdin/stdout are actually open
        if self._connection == STDIO: return False

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._sock.connect((self._host, self._port))
        except socket.error, e:
            self.DEBUG("socket error",DBG_CONN_ERROR)
            raise error(e)

        if self._connection == TCP_SSL:
            try:
                self.DEBUG("Attempting to create ssl socket",DBG_INIT)
                self._sslObj    = socket.ssl( self._sock, None, None )
                self._sslIssuer = self._sslObj.issuer()
                self._sslServer = self._sslObj.server()
            except:
                self.DEBUG("Socket Error: No SSL Support",DBG_CONN_ERROR)
                raise error("No SSL Support")

        self.DEBUG("connected",DBG_INIT)
        self.header()
        return True

class Server:    

    def now(self): return time.ctime(time.time())

    def __init__(self, maxclients=10):

        self.host = ''  
        self.port = 5222
        self.streams = []
            
        # make main sockets for accepting new client requests
        self.mainsocks, self.readsocks, self.writesocks = [], [], []

        self.portsock = socket(AF_INET, SOCK_STREAM)
        self.portsock.bind((self.host, self.port)) 
        self.portsock.listen(maxclients)           
                
        self.mainsocks.append(self.portsock)  # add to main list to identify
        self.readsocks.append(self.portsock)  # add to select inputs list 
                
        # event loop: listen and multiplex until server process killed


    def serve(self):
        
        print 'select-server loop starting'
        
        while 1:
            print "LOOPING"
            readables, writeables, exceptions = select(self.readsocks,
                                                       self.writesocks, [])
            for sockobj in readables:
                if sockobj in self. mainsocks:   # for ready input sockets
                    newsock, address = sockobj.accept() # accept not block
                    print 'Connect:', address, id(newsock) 
                    self.readsocks.append(newsock)
                    self._makeNewStream(newsock)
                    # add to select list, wait
                else:
                    # client socket: read next line
                    data = sockobj.recv(1024)
                    # recv should not block
                    print '\tgot', data, 'on', id(sockobj)
                    if not data:        # if closed by the clients 
                        sockobj.close() # close here and remv from
                        self.readsocks.remove(sockobj) 
                    else:
                    # this may block: should really select for writes too
                        sockobj.send('Echo=>%s' % data)

    def _makeNewStream(self, sckt):
        new_stream = Stream('localhost', 5222,
                            'jabber:client',
                            sock=sckt)
        self.streams.append(new_stream)
                            ## maybe overide for a 'server stream'
        new_stream.header()
        return new_stream

    def _getStreamSockets(self):
        socks = [];
        for s in self.streams:
            socks.append(s.getSocket())
        return socks
        
    def _getStreamFromSocket(self, sock):
        for s in self.streams:
            if s.getSocket() == sock:
                return s
        return None

