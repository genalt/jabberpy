##   debug.py 
##
##   Copyright (C) 2003 Jacob Lundqvist
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
Debuging for jabber.py and xmlstream

Other modules can always define extra debug flags for local usage, as long as
they make sure they append them to debug_flags

Also its always a good thing to prefix local flags with something, to reduce risk
of coliding flags


"""


import sys
from string import join

VERSION = '1.0.1'

debug_flags = []

"""
 The reason for having a double statement is so we can validate params
 at init and catch all undefined debug flags
 
 group flags, that is a flag in it self containing multiple flags should be
 defined without the debug_flags.append() sequence, since the parts are already
 in the list
 example:
  DBG_MULTI = [ DBG_INIT,DBG_CONNECTION ]
 
"""

DBG_INIT = 'init'                ; debug_flags.append( DBG_INIT )
DBG_CONNECTION = 'connection'    ; debug_flags.append( DBG_CONNECTION )

"""
 DEBUG_ALWAYS is a special case and has two meanings, 

 if given to init, everything will be shown regardless of actual flag
 for that call

 If given for a specific call, that call will be displayed as long as there
 are any debugging specified at all. 

 This is also the default, so if flag is not specified for a call, 
 that message will be shown as long as debuging is active at all.
"""
DBG_ALWAYS = 'always'   ; debug_flags.append( DBG_ALWAYS )



"""
       Jabberpy related flags
"""





class Debug:
    def __init__( self,
                  active_flags = None, 
                  log_file = sys.stderr,
                  #
                  # flag_show should normaly be of, but can be turned on to get a
                  # good view of what flags are actually used for calls,
                  # if it is not None, it should be a string
                  # flags for current call will be displayed 
                  # with flag_show as separator
                  # recomended values vould be '-' or ':', but any string goes
                  flag_show = None,
                  #
                  # prefix and sufix can either be set globaly or per call.
                  # personally I use this to color code debug statements
                  # with prefix = chr(27) + "[34m"
                  #      sufix = chr(27) + "[37;1m\n"
                  prefix = 'DEBUG: ', 
                  sufix = '\n',
                  ):
        # firtst prepare output
        if log_file:
            if type( log_file ) is type(""):
                try:
                    self._fh = open(log_file,'w')
                except:
                    print "ERROR: can open %s for writing"
                    sys.exit(0)
            else: ## assume its a stream type object
                self._fh = log_file
        else:
            self._fh = sys.stdout
         
        self.flag_show = None # see below for explanation...
        self.prefix = prefix
        self.sufix = sufix
        
        if not active_flags:
            self.active = []
        elif type( active_flags ) == type([]):
            ok_flags = []
            # pass 1, split all group flags given to init in its parts
            flags = self._as_one_list( active_flags )
            for t in flags:
                if t not in debug_flags:
                    raise 'Invalid debugflag given', t
                ok_flags.append( t )
                
            self.active = ok_flags
            self.show('')
            self.show('Debug flags defined: %s' % join( self.active ))
        else:
            self.active = [ DBG_ALWAYS ]
            self.show( '***' )
            self.show( '*** Invalid or oldformat debug param given: %s' % active_flags )
            self.show( '*** please correct your param, should be of [] type!' )
            self.show( '*** due to this, full debuging is enabled' )

        # define this after init msgs, we dont want to display flags for
        # init calls to show()
        if type(flag_show) in ( type(''), type(None)):
            self.flag_show = flag_show
        else:
            msg2 = "%s" % type(flag_show )
            raise "Invalid type for flag_show!", msg2

    def show( self, msg, flag = DBG_ALWAYS, prefix = None, sufix = None ):
        """
        flag can be of folowing types:
            None - interpreted as DBG_ALWAYS, if any debugging is on, it will be shown
            flag - will be shown if flag is active, or global DBG_ALWAYS is defined
            (flag1,flag2,,,) - will be shown if any of the given flags are active or
                               global DBG_ALWAYS is defined
        """
        if self.is_active(flag):
            if prefix:
                pre = prefix
            else:
                pre = self.prefix
            if sufix:
                suf = sufix
            else:
                suf = self.sufix
            if self.flag_show:
                msg = "%s%s%s" % (flag, self.flag_show, msg )
            try:
                self._fh.write("%s%s%s" % ( pre, msg, suf ))
            except:
                # unicode strikes again ;)
                s=u''
                for i in range(len(msg)):
                    if ord(msg[i]) < 128:
                        c = msg[i]
                    else:
                        c = '?'
                    s=s+c
                self._fh.write("%s%s%s" % ( pre, s, suf ))
            self._fh.flush()
            
                
    def is_active( self, flag ):
        "If given flag should generate output."

        # try to abort early to quicken code
        if not self.active:
            return 0
        elif flag == DBG_ALWAYS or DBG_ALWAYS in self.active or flag in self.active:
            return 1
        else:
            # check for multi flag type:
            if type( flag ) == type(()):
                for s in flag:
                    if s in self.active:
                        return 1
        return 0

    
    def _as_one_list( self, lst ):
        """ init param might contain nested lists, typically from group flags.
        
        This code organises lst and remves dupes
        """
        r = []
        for l in lst:
            if type( l ) == type([]):
                lst2 = self._as_one_list( l )
                for l2 in lst2: 
                    self._append_unique(r, l2 )
            else:
                self._append_unique(r, l )
        return r
            
    def _append_unique( self, lst, item ):
        "filter out any dupes"
        if item not in lst:
            lst.append( item )
        return lst

    def __del__( self ):
        if self._fh not in ( sys.stderr, sys.stdout ):
            self._fh.close()
