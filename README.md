# foobartory
`foobartory` is a robots factory. 
Robot can build materials like "foo" and "bar", they can build another robot from materials. 
Robot can also sell/buy other robots.

# Design Principles
Concurrent tasks run on asyncio library, asyncio queue is used to manage shared ressources between coroutines.

# Launch foobartory
Require `Python 3.8` \
Launch with `python foobartory.py` \
`EXEC_SPEED` variable from `foobartory.py` configure execution speed of the program.
