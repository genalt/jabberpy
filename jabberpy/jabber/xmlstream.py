##   xmlstream.py 
##
##   Copyright (C) 2001 Matthew Allum
##
##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##

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

import xmllib, time, sys, re
import socket
from select import select
from string import split,find,replace
import xml.parsers.expat

VERSION = 0.2

False = 0;
True  = 1;

def XMLescape(txt):
    "Escape XML entities"
    replace(txt, "&", "&amp;")
    replace(txt, "<", "&lt;")
    replace(txt, ">", "&gt;")
    return txt

def XMLunescape(txt):
    "Unescape XML entities"
    replace(txt, "&amp;", "&")
    replace(txt, "&lt;", "<")
    replace(txt, "&gt;", ">")
    return txt

class error:
    def __init__(self, value):
        self.value = str(value)
    def __str__(self):
        return self.value
    
class Node:
    """A simple XML DOM like class"""
    def __init__(self, tag='', parent=None, attrs=None ):
        bits = split(tag)
        if len(bits) == 1:
            self.name = tag
            self.namespace = ''
        else:
            self.namespace, self.name = bits

        if attrs is None:
            self.attrs = {}
        else:
            self.attrs = attrs
            
        self.data = ''
        self.kids = []
        self.parent = parent
        
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
        self.data = data

    def insertData(self, data):
        "Set the nodes textual data" 
        self.data = data

    def getData(self):
        "Return the nodes textual data" 
        return self.data

    def getNamespace(self):
        "Returns the nodes namespace." 
        return self.namespace

    def setNamespace(self, namespace):
        "Set the nodes namespace." 
        self.namespace = namespace

    def insertTag(self, name):
        "Add a child tag of name 'name' to the node"
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
        s = s + ">" + XMLescape(self.data)
        if self.kids != None:
            for a in self.kids:
                s = s + a._xmlnode2str(parent=self)
        s = s + "</" + self.name + ">"
        return s

    def getTag(self, name):
        """Returns a child node with tag name name. Returns None
        if not found."""
        for node in self.kids:
            if node.getName() == name:
               return node
        return None

    def getChildren(self):
        """Returns a nodes children"""
        return self.kids

class NodeBuilder:
    """builds a 'minidom' from data parsed to it. Primarily for insertXML
       method of Node"""
    def __init__(self,data):
        self._parser = xml.parsers.expat.ParserCreate(namespace_separator=' ')
        self._parser.StartElementHandler  = self.unknown_starttag
        self._parser.EndElementHandler    = self.unknown_endtag
        self._parser.CharacterDataHandler = self.handle_data

        self.__depth = 0
        self.__done  = 0 #needed ?
        self.__space_regex = re.compile('^\s+$')
        
        self._parser.Parse(data,1)

    def unknown_starttag(self, tag, attrs):
        self.__depth = self.__depth + 1
        if self.__depth == 1:
            self._mini_dom = Node(tag=tag, attrs=attrs)
            self._ptr = self._mini_dom
        elif self.__depth > 1:
            self._ptr.kids.append(Node(tag=tag, parent=self._ptr,attrs=attrs ))
            self._ptr = self._ptr.kids[-1]
        else:                           ## fix this ....
            pass 

    def unknown_endtag(self, tag ):
        self.__depth = self.__depth - 1
        if self.__depth == 0:
            self.dispatch(self._mini_dom)
        elif self.__depth > 0:
            self._ptr = self._ptr.parent
        else:
            pass

    def handle_data(self, data):
        if not self.__space_regex.match(data):  ## check its not all blank 
            self._ptr.data = self._ptr.data + data 

    def dispatch(self,dom):
        self.__done = 1

    def getDom(self):
        return self._mini_dom


class Client:
    def __init__(self, host, port, namespace, debug=True, log=None):
        self._parser = xml.parsers.expat.ParserCreate(namespace_separator = ' ')
        self._parser.StartElementHandler  = self._unknown_starttag
        self._parser.EndElementHandler    = self._unknown_endtag
        self._parser.CharacterDataHandler = self._handle_data

        self._host = host
        self._port = port 
        self._namespace = namespace
        self.__depth = 0
        self.__sock = None

        self._streamID = None
        
        self._debug = debug

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
        
        
    def DEBUG(self,txt):
        if self._debug:
            sys.stderr.write("DEBUG: %s\n" % txt)

    def connect(self):
        """Attempt to connect to specified host"""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__sock.connect((self._host, self._port))
        except socket.error, e:			  
            raise error(e)
            return 0
        self.DEBUG("connected")
        str = u"<?xml version='1.0' ?>                \
               <stream:stream to='%s' xmlns='%s'      \
                xmlns:stream='http://etherx.jabber.org/streams'>" % \
               ( self._host, self._namespace )
        self.write (str)
        self.read()

    def _handle_data(self, data):
        """XML Parser callback"""
        self.DEBUG("data-> " + data)
        ## TODO: get rid of empty space
        self._ptr.data = self._ptr.data + data 
        
    def _unknown_starttag(self, tag, attrs):
        """XML Parser callback"""
        self.__depth = self.__depth + 1
        self.DEBUG("DEPTH -> %i , tag -> %s, attrs -> %s" % \
                   (self.__depth, tag, str(attrs)) )
        if self.__depth == 2:
            self._mini_dom = Node(tag=tag, attrs=attrs)
            self._ptr = self._mini_dom
        elif self.__depth > 2:
            self._ptr.kids.append(Node(tag=tag,parent=self._ptr,attrs=attrs))
            self._ptr = self._ptr.kids[-1]
        else:                           ## it the stream tag:
            if attrs.has_key('id'):
                self._streamID = attrs['id']

    def _unknown_endtag(self, tag ):
        """XML Parser callback"""
        self.__depth = self.__depth - 1
        self.DEBUG("DEPTH -> %i" % self.__depth)
        if self.__depth == 1:
            self.dispatch(self._mini_dom)
        elif self.__depth > 1:
            self._ptr = self._ptr.parent
        else:
            self.DEBUG("*** Server closed connection ? ****")

    def dispatch(self, nodes, depth = 0):
        """Overide with the method you want to called with
        a node structure of a 'protocol element."""

        padding = ' '
        padding = padding * depth
        depth = depth + 1
        for n in nodes:
            print padding + "name => " + n.name
            print padding + "attrs => " , n.attrs
            print padding + "data  => " , n.data
            if n.kids != None:
                self.dispatch(n.kids, depth)
                
    ##def syntax_error(self, message):
    ##    self.DEBUG("error " + message)

    def read(self):
        """Reads incoming data. Called by process() so nonblocking"""
        data = u''
        data_in = self.__sock.recv(1024)
        while data_in:
            data = data + data_in
            if len(data_in) != 1024:
                break
            data_in = self.__sock.recv(1024)
        self.DEBUG("got data %s" % data )
        self.log(data, 'RECV:')
        self._parser.Parse(data)
        return data
    
    def write(self,data_out=''):
        """Writes raw outgoing data. blocks"""
        self.DEBUG("sending %s" % data_out)
        try:
            self.__sock.send (data_out)
            self.log(data_out, 'SENT:')
        except:
            self.disconnected()
            
    def process(self,timeout):
         ready_for_read,ready_for_write,err = \
                        select([self.__sock],[],[],timeout)
         for s in ready_for_read:
             if s == self.__sock:
                 if not len(self.read()):# A read of length 0 means disconnect
                     self.disconnected()
                     return False
                 return True
         return False

    def disconnect(self):
        """Close the stream and socket"""
        time.sleep(1) ## sleep for a second - server bug ? ##        
        self.write ( "</stream:stream>" )
        self.__sock.close()
        self.__sock = None
        
    def disconnected(self): ## To be overidden ##
        """Called when a Network Error or disconnection occurs.
        Designed to be overidden"""
        self.DEBUG("Network Disconnection")
        pass

    def log(self, data, inout=''):
        """Logs data to the specified filehandle. Data is time stamped
        and prefixed with inout"""
        if self._logFH is not None:
            self._logFH.write("%s - %s - %s\n" %           
            (time.asctime(time.localtime(time.time())), inout, data ) )
        
    def getStreamID(self):
        """Returns the streams ID"""
        return self._streamID

class Server:    
    pass

class Stream:
    ## this will form a base for both Client and Server 
    pass










