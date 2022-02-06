# foobartory
`foobartory` is a robots factory.  \
Robots can : \
-Mine _foo_, takes 1 second. \
-Mine _bar_, takes between 0.5 and 2 seconds. \
-Make _foobar_, takes 2 seconds. Require 1 _foo_ and 1 _bar_. Success rate is 60%, if it fails _bar_ is returned not _foo_. \
-Sell _foobar_, takes 10 seconds. They can sell between 1 to 5 _foobar_ at a time and get 1 _money_ by sold _foobar_. \
-Buy _Robot_, takes no time. Requires 3 _money_ and 6 _foo_.

The factory starts with 2 robots. \
The goal of the factory is to produce 30 _foobar_ then factory is stopped.

# Design Principles
To optimize the factory, a robot wich is waiting to process his task must not block others robots to process their task. Asyncio is suited to run concurrent code.
Robots choose they task randomly depending ressources available.

# Code quality
Style/Code consistency : pylint/flake8
Sorting imports: isort
Formatting code: black

# Launch foobartory
-Run on Windows and Linux. \
-Require `Python 3.8` (Needed to store name of task: create_task from asyncio eventloop require name parameter: https://docs.python.org/3.8/library/asyncio-task.html#asyncio.create_task)
```
usage: foobartory.py [-h] [--speed SPEED]

Foobar factory.

options:
  -h, --help     show this help message and exit
  --speed SPEED  Set execution speed of factory. "One factory second" = "One real second"/EXEC_SPEED
usage: foobartory.py [-h] [--speed SPEED]

Foobar factory.

options:
  -h, --help     show this help message and exit
  --speed SPEED  Set execution speed of factory. "One factory second" = "One real second"/EXEC_SPEED
```

# If I had more time...
-Add tests \
-Add fancy UI with Robot/ressources animations \
-Add an optimized strategy to get the 30 foobar the quickest way possible, maybe with machine learning (runs program several times, and construct a model of optmized next task).

# Limitations
-It may happen that a ressource is not anymore available when robots are waiting to process their task. It would be better to get ressource before waiting that the task end.
