#!/usr/bin/env python2
"""
jrpc demonstrates extending an iq with the QueryPayload methods.

This example, using xmlrpclib, simply wraps an XML-RPC request
a an ip with the namespace 'jabber:iq:rpc'

For more info on this technique see http://www.pipetree.com/jabber/jrpc.html 

mallum <breakfast@10.am>
"""

## Import Jabber modules
import Jabber
import XMLStream

## Import xmlrpclib - http://www.pythonware.com/products/xmlrpc/index.htm 
import xmlrpclib
import sys

## This is called when an Iq is recieved 
def iqCB(con,iq):
    queryNS = iq.getQuery()
    ## Get the query part of the Iq and check its namespace and id
    if queryNS == 'jabber:iq:rpc' and iq.getID() == '999999':
        ## Get the querys 'payload' , will return an XMLStreanNode structure
        xmlrpc_node = iq.getQueryPayload()
        ## Let xmlrpclib parse the method call. The node becomes a string
        ## automatically when called in a str context. 
        params,func = xmlrpclib.loads("<?xml version='1.0'?>%s" % xmlrpc_node)
        ## Print the function name and params xmllibrpc returns
        print "Recieved -> ",func,params
        ## Exit
        sys.exit()


## Setup server and auth varibles
## You'll need to edit these. 
Server   = 'jabber.com'
Username = 'XXXXXX'
Password = 'XXXXXX'
Resource = 'xmlrpc'

## Get a Jabber connection object, with loging to stderr
con = Jabber.Connection(host=Server,log=sys.stderr)

## Try and connect
try:
    con.connect()
except XMLStream.error, e:
    print "Couldn't connect: %s" % e
    sys.exit(0)
else:
    print "Connected"

## Attatch the above iq callback
con.setIqHandler(iqCB)

## Authenticate
if con.auth(Username,Password,Resource):
    print "Authenticated"
else:
    print "Auth failed", con.lastErr, con.lastErrCode
    sys.exit(1)

## Get the roster and send presence. Maybe not needed but
## good practise.
con.requestRoster()
con.sendInitPresence()

## Build an XML-RPC request - note xmlrpc_req is a string
xmlrpc_req = xmlrpclib.dumps( (1,2,'three'), methodname='test_func' )

## Birth an iq ojbject to send to self
iq = Jabber.Iq(to="%s@%s/%s" % ( Username, Server, Resource), type="get")

## Set the i'qs query namespace
iq.setQuery('jabber:iq:rpc')

## Set the ID
iq.setID('999999')

## Set the query payload - can be an XML document or
## a XMLStreamNode structure
iq.setQueryPayload(xmlrpc_req)

## Send it
con.send(iq)

## wait .... 
while 1: con.process(1)

