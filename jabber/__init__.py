__all__ = []

import jabber

for __s in dir(jabber):
    __val = getattr(jabber, __s)
    globals()[__s] = __val
    __all__.append(__val)

del __s, __val
