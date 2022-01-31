# foobartory
`foobartory` is a robots factory. 
Robot can build materials like "foo" and "bar", they can build another robot from materials. 
Robot can also sell/buy other robots.

# Design Principles
Concurrent tasks run with asyncio library, asyncio queue is used to manage shared ressources between coroutines.

# Launch foobartory
Run on Windows and Linux
Require `Python 3.8` \
Launch command : `python foobartory.py` \
`EXEC_SPEED` variable from `foobartory.py` configure execution speed of the program.
