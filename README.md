# foobartory
`foobartory` is a robots factory. 
Robot can build materials like "foo" and "bar", they can build another robot from materials. 
Robot can also sell/buy other robots.

# Design Principles
Concurrent tasks run with asyncio library, asyncio queue is used to manage shared ressources between coroutines.

# Launch foobartory
Run on Windows and Linux, \
require `Python 3.8`, \
launch command : `python foobartory.py`, \
`EXEC_SPEED` variable from `foobartory.py` set execution speed. Default EXEC_SPEED value : 1. Set EXEC_SPEED = 1000 to get quick result.
