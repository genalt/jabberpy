# XML stream library for clients and servers
# implemented in Python.

"""\
Documentation will be here


"""
import xmllib, time, sys
#from socket import socket
import socket
from select import select
from string import split,find,replace
import xml.parsers.expat

False = 0;
True  = 1;

class error:
    def __init__(self, value):
        self.value = str(value)
    def __str__(self):
        return self.value
    

class XMLStreamNode:
    def __init__(self,tag='',attrs={}, parent=None, data=''):
        bits = split(tag)
        if len(bits) == 1:
            self.name = tag
            self.namespace = ''
        else:
            self.namespace, self.name = bits
        print "NAMESPACE: " + self.namespace
        self.attrs = attrs
        self.data = data
        self.kids = []
        self.parent = parent
        
    def setParent(self, node):
        self.parent = node

    def getParent(self):
        return self.parent

    def getName(self):
        return self.name

    def setName(self,val):
        self.name = val

    def putAttr(self, key, val):
        self.attrs[key] = val

    def getAttr(self, key):
        return self.attrs[key]

    def putData(self, data):
        self.data = data

    def getData(self):
        return self.data

    def insertTag(self, name):
        newnode = XMLStreamNode(tag=name, attrs={}, parent=self)
        self.kids.append(newnode)
        return newnode

    def __str__(self):
        return self._xmlnode2str()

    def _xmlnode2str(self):
        str = "<" + self.name   # should I call get_name() ?
        for a in self.attrs.keys():
            str = str + " " + a + "='" + self.attrs[a] + "'"
        str = str + ">" + self.data
        if self.kids != None:
            for a in self.kids:
                str = str + a._xmlnode2str()
        str = str + "</" + self.name + ">"
        return str

    def getTag(self, name):
        for node in self.kids:
            if node.getName() == name:
               return node
        return None

    def getChildren(self):
        return self.kids


class Client:
    def __init__(self, host, port, namespace, debug=True, log=False):
        self._parser = xml.parsers.expat.ParserCreate(namespace_separator = ' ')
        self._parser.StartElementHandler  = self.unknown_starttag
        self._parser.EndElementHandler    = self.unknown_endtag
        self._parser.CharacterDataHandler = self.handle_data

        self._host = host
        self._port = port 
        self._namespace = namespace
        self.__depth = 0
        self.__sock = None
        
        self._debug = debug
        self._doLog = log
        self._logData   = ''
        
    def DEBUG(self,txt):
        if self._debug:
            print "DEBUG: %s" % txt

    def connect(self):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__sock.connect((self._host, self._port))
        except socket.error, e:			  
            raise error(e)
            return 0
        self.DEBUG("connected")
        str = u"<?xml version='1.0' ?>                \
               <stream:stream to='%s' xmlns='%s'                      \
                xmlns:stream='http://etherx.jabber.org/streams'>" %   \
               ( self._host, self._namespace )
        self.write (str)
        self.read()

    def handle_data(self, data):
        self.DEBUG("data-> " + data)
        self._ptr.data = self._ptr.data + data 
        
    def unknown_starttag(self, tag, attrs):
        self.__depth = self.__depth + 1
        self.DEBUG("DEPTH -> %i , tag -> %s" % (self.__depth, tag) )
        if self.__depth == 2:
            self._mini_dom = XMLStreamNode(tag,attrs)
            self._ptr = self._mini_dom
        elif self.__depth > 2:
            self._ptr.kids.append(XMLStreamNode(tag,attrs,self._ptr))
            self._ptr = self._ptr.kids[-1]
        else:                           ## self.depth == 1:
            pass

    def unknown_endtag(self, tag ):
        self.__depth = self.__depth - 1
        self.DEBUG("DEPTH -> %i" % self.__depth)
        if self.__depth == 1:
            self.dispatch(self._mini_dom)
        elif self.__depth > 1:
            self._ptr = self._ptr.parent
        else:
            self.DEBUG("*** Server closed connection ? ****")

    def dispatch(self, nodes, depth = 0):
        """Im here to be overiden"""

        padding = ' '
        padding = padding * depth
        depth = depth + 1
        for n in nodes:
            print padding + "name => " + n.name
            print padding + "attrs => " , n.attrs
            print padding + "data  => " , n.data
            if n.kids != None:
                self.dispatch(n.kids, depth)
                
    def syntax_error(self, message):
        self.DEBUG("error " + message)

    def read(self):
        data = ''
        data_in = self.__sock.recv(1024)
        while data_in:
            data = data + data_in
            if len(data_in) != 1024:
                break
            data_in = self.__sock.recv(1024)
        self.DEBUG("got data %s" % data )
        self.log(data, '<--')
        self._parser.Parse(data)
        return data
    
    def write(self,data_out=''):
        self.DEBUG("sending %s" % data_out)
        self.__sock.send (data_out)
        self.log(data_out, '-->')
        
    def process(self,timeout):
         ready_for_read, ready_for_write, err = select([self.__sock],[self.__sock],[],timeout)
         if err:
             self.DEBUG("select returned an err")
         for s in ready_for_read:
             if s == self.__sock:
                 self.read()
                 return True
         return False

    def disconnect(self):
        self.write ( "</stream:stream>" )
        self.__sock.close()
        self.__sock = None
        
    def disconnected(self): ## To be overidden ##
        pass

    def XMLescape(self,txt):
        replace(txt, "&", "&amp;")
        replace(txt, "<", "&lt;")
        replace(txt, ">", "&gt;")
        return txt

    def XMLunescape(self,txt):
        replace(txt, "&amp;", "&")
        replace(txt, "&lt;", "<")
        replace(txt, "&gt;", ">")
        return txt

    def clearLog(self):
        self._logData = ''

    def log(self, data, inout):
        if self._doLog:
            self._logData = self._logData + \
               "%s - %s - %s" %           \
            (time.asctime(time.localtime(time.time())), \
             inout, data )
        
    def getLog(self):
        return self._logData


class Server:    
    pass ## muhahahahah








