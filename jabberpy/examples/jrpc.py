#!/usr/bin/env python2
"""
jrpc demonstrates extending an iq with the QueryPayload methods.

This example, using xmlrpclib, simply wraps an XML-RPC request
a an ip with the namespace 'jabber:iq:rpc'

For more info on this technique see http://www.pipetree.com/jabber/jrpc.html 

mallum <breakfast@10.am>
"""

# $Id$

import sys

## Import jabber module
import jabber

## Import xmlrpclib - http://www.pythonware.com/products/xmlrpc/index.htm 
import xmlrpclib

## Setup server and auth varibles
## You'll need to edit these. 
Server   = 'jabber.com'
Username = 'xxxx'
Password = 'xxxx'
Resource = 'xmlrpc'

IqID     = '999999'

def iq_CB(con,iq):
    print "got an iq"

def iq_error_CB(con,iq):
    print "got an error -> ", iq.getError()
    
## This is called when an Iq is recieved 
def iq_xmlrpc_response_CB(con,iq):

    ## Get the query part of the Iq and check its namespace and id
    if iq.getID() == IqID:

        ## Get the querys 'payload' , will return an XMLStreanNode structure
        xmlrpc_node = iq.getQueryPayload()

        ## Let xmlrpclib parse the method call. The node becomes a string
        ## automatically when called in a str context. 
        result,func = xmlrpclib.loads("<?xml version='1.0'?>%s" % xmlrpc_node)

        ## Print the function name and params xmllibrpc returns
        print "Recieved -> ",result

        ## Exit
        sys.exit()



## Get a jabber connection object, with logging to stderr
con = jabber.Client(host=Server,log=sys.stderr)

## Try and connect
try:
    con.connect()
except:
    print "Couldn't connect: %s" % e
    sys.exit(0)
else:
    print "Connected"

## Attatch the above iq callback
con.setIqHandler(iq_CB)
con.setIqHandler(iq_error_CB, type='error')
con.setIqHandler(iq_xmlrpc_response_CB, type='get', ns='jabber:iq:rpc')

## Authenticate
if con.auth(Username,Password,Resource):
    print "Authenticated"
else:
    print "Auth failed", con.lastErr, con.lastErrCode
    sys.exit(1)

## Get the roster and send presence. Maybe not needed but
## good practise.
## con.requestRoster()
## con.sendInitPresence()

## Build an XML-RPC request - note xmlrpc_req is a string
params = ( (16,2,7,4), )
method = 'examples.getStateList'
print "sending ", method, params
xmlrpc_req = xmlrpclib.dumps( params , methodname=method)

## Birth an iq ojbject to send to self
iqTo = "jrpchttp.gnu.mine.nu/http://validator.userland.com:80/RPC2"
iq = jabber.Iq(to=iqTo, type="set")

## Set the i'qs query namespace
iq.setQuery('jabber:iq:rpc')

## Set the ID
iq.setID(IqID)

## Set the query payload - can be an XML document or
## a Node structure
iq.setQueryPayload(xmlrpc_req)

## Send it
con.send(iq)

## wait .... 
while 1: con.process(1)

