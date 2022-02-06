"""
foobartory: automatic foobar production line.
"""
import asyncio
from enum import Enum
import signal
import os
import logging
import random

# "One factory second" = "One real second"/EXEC_SPEED
SPEED = int(os.getenv('EXEC_SPEED', '1'))

# Logging configuration
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)

class RobotTask(Enum):
    """
    Enum RobotTask : describe robot abilities
    """
    NONE = 0
    MINING_FOO = 1
    MINING_BAR = 2
    MAKE_FOOBAR = 3
    SELL_FOOBAR = 4
    BUY_ROBOT = 5

class InventoryManager():
    """
    The InventoryManager object store ressources of factory : foo, bar, money.
    Store also locks for accessing ressources.
    """
    def __init__(self) -> None:
        # Ressources counter
        self.res_foo = 1
        self.res_bar = 1
        self.res_money = 0
        self.res_foobar = 0

        # Maintain consistency of ressources
        self.lock_res_foo = asyncio.Lock()
        self.lock_res_bar = asyncio.Lock()
        self.lock_money = asyncio.Lock()
        self.lock_res_foobar = asyncio.Lock()

        # Robots
        self.robots_list = []

class Robot():
    """
    The Robot object store coroutine to make foo/bar, and build/sell/buy robots.
    """
    def __init__(self, inventory_manager :"InventoryManager", name):
        self._previous_task = RobotTask.NONE
        self._im = inventory_manager
        self.name = name

    def _next_task(self):
        res_foo =self._im.res_foo
        res_bar = self._im.res_bar
        res_money = self._im.res_money
        res_foobar = self._im.res_foobar
        logger.info('foo : %s, bar : %s, money : %s, foobar : %s', res_foo, res_bar, res_money, res_foobar) # pylint: disable=line-too-long

        list_available_task = [RobotTask.MINING_BAR, RobotTask.MINING_FOO]

        # Can make foobar
        if res_foo and res_bar:
            list_available_task.append(RobotTask.MAKE_FOOBAR)

        # Can sell foobar
        if res_foobar > 1:
            list_available_task.append(RobotTask.SELL_FOOBAR)

        # Can buy robot
        if res_money >= 3 and res_foo >= 6:
            list_available_task.append(RobotTask.BUY_ROBOT)

        # Return randomly one task from list_available_task
        return random.choice(list_available_task)

    async def work(self):
        """
        Coroutine robot task
        """
        try:
            while True:
                # Choose the next task randomly
                next_task = self._next_task()

                # Robot moving time
                if (next_task is not self._previous_task) and self._previous_task:
                    logger.info('%s is moving to new task', self.name)
                    await asyncio.sleep(5/SPEED)
                self._previous_task = next_task

                # Run the task
                if next_task is RobotTask.MINING_FOO:
                    await self.mining_foo()
                elif next_task is RobotTask.MINING_BAR:
                    await self.mining_bar()
                elif next_task is RobotTask.MAKE_FOOBAR:
                    await self.make_foobar()
                elif next_task is RobotTask.SELL_FOOBAR:
                    await self.sell_foobar()
                elif next_task is RobotTask.BUY_ROBOT:
                    await self.buy_robot()

        except asyncio.CancelledError:
            logger.warning('%s cancelled', self.name)
        else:
            return 1

    async def mining_foo(self):
        """
        Mining foo: takes 1 second.
        """
        logger.info('%s START mining foo', self.name)
        await asyncio.sleep(1/SPEED)
        async with self._im.lock_res_foo:
            self._im.res_foo+=1
        logger.info('%s END mining foo', self.name)

    async def mining_bar(self):
        """
        Mining bar: takes between 0.5 and 2 seconds
        """
        logger.info('%s START mining bar', self.name)
        await asyncio.sleep((random.randint(5,20)/10.0)/SPEED)
        async with self._im.lock_res_bar:
            self._im.res_bar+=1
        logger.info('%s END mining bar', self.name)

    async def make_foobar(self):
        """
        Making foobar: takes 2 seconds.
        Require 1 foo and 1 bar.
        Success rate : 60%.
        If it fails return bar not foo.
        """
        logger.info('%s START make foobar', self.name)
        await asyncio.sleep(2/SPEED)

        async with self._im.lock_res_foo, self._im.lock_res_bar:
            if self._im.res_foo and self._im.res_bar:
                self._im.res_foo-=1
                self._im.res_bar-=1
            else:
                logger.warning('%s Make foobar: ressources unavailable', self.name)
                return

        # success make foobar : 60% chance of success
        if random.randint(1,10) <= 6:
            # success
            async with self._im.lock_res_foobar:
                self._im.res_foobar+=1
            logger.info('%s END make foobar: success', self.name)
        else:
            # fail -> Give back bar not foo
            async with self._im.lock_res_bar:
                self._im.res_bar+=1
            logger.warning('%s END make foobar: fail', self.name)

    async def sell_foobar(self):
        """
        Sell foobar: takes 10 seconds.
        Robot can sell between 1 to 5 foobar.
        Get 1 money by sold foobar.
        """
        logger.info('%s START sell foobar', self.name)
        await asyncio.sleep(10/SPEED)

        async with self._im.lock_res_foobar, self._im.lock_money:
            if self._im.res_foobar:
                nb_foobar_sold = random.randint(1,min(5, self._im.res_foobar))
                self._im.res_money+=nb_foobar_sold
                self._im.res_foobar-=nb_foobar_sold
                logger.info('%s END sell %s foobar', self.name, nb_foobar_sold)
            else:
                logger.warning('%s Sell foobar: ressources unavailable', self.name)

    async def buy_robot(self):
        """
        Buy robot: takes not time.
        Cost : 3 money and 6 foo.
        """
        logger.info('%s START buy robot', self.name)
        async with self._im.lock_money, self._im.lock_res_foo:
            if self._im.res_money >= 3 and self._im.res_foo >=6:
                self._im.res_money-=3
                self._im.res_foo-=6
            else:
                logger.warning('%s Buy robot : ressources unavailable', self.name)
        logger.info('%s END buy robot', self.name)

        await self.create_robot_task()

    async def create_robot_task(self):
        """
        Create new robot task: add new coroutine to asyncio loop.
        Terminate factory when 30 robots are runing.
        """
        robot_id = len(self._im.robots_list) + 1
        robot_alive = Robot(self._im ,name=f'Robot {robot_id}')
        self._im.robots_list.append(robot_alive)
        running_loop = asyncio.get_running_loop()
        running_loop.create_task(robot_alive.work(), name=f'Robot {robot_id}')

        # Stop runing loop when we have enough robots
        if len(self._im.robots_list) == 30:
            terminate_factory()

def terminate_factory():
    """
    Terminate factory: cancel all runing tasks in asyncio loop and stop the loop
    """
    logger.info('Terminate factory. The last %s working robots are :', len(asyncio.all_tasks()))
    for task in asyncio.all_tasks():
        logger.info(task.get_name())
        task.cancel()

    asyncio.get_running_loop().stop()

def exit_gracefully(signum, frame):
    """
    Catch CTRL+C input keyboard and terminate factory
    """
    signal.signal(signal.SIGINT, original_sigint)
    terminate_factory()

    # restore the exit gracefully handler
    signal.signal(signal.SIGINT, exit_gracefully)

# Redirect SIGINT to exit gracefully
original_sigint = signal.getsignal(signal.SIGINT)
signal.signal(signal.SIGINT, exit_gracefully)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

im = InventoryManager()

for i in range(2):
    robot = Robot(im, name=f'Robot {i}')
    im.robots_list.append(robot)
    loop.create_task(robot.work(), name=robot.name)
try:
    loop.run_forever()
except: # pylint: disable=bare-except
    loop.close()
