#!/usr/bin/env python2
import sys

try:
    from distutils.core import setup
except:
    if sys.version[0] < 2:
        print "jabber.py requires at least python 2.0"
        print "Setup cannot continue."
        sys.exit(1)
    print "You appear not to have the Python distutils modules"
    print "installed. Setup cannot continue."
    print "You can manually install jabber.py by copying jabber.py"
    print "and xmlstream.py to your /python-libdir/site-packages"
    print "directory."
    sys.exit(1)
    
setup(name="jabber.py",
      version="0.3-1",
      py_modules=["xmlstream","jabber"],
      description="Python xmlstream and jabber IM protocol libs",
      author="Matthew Allum",
      author_email="breakfast@10.am",
      url="http://jabberpy.sf.net/",
      license="LGPL"
      )






