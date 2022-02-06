"""
foobartory: automatic foobar production line.
"""
import argparse
import asyncio
import itertools
import logging
import random
import signal
from enum import Enum

# "One factory second" = "One real second"/EXEC_SPEED
parser = argparse.ArgumentParser(description="Foobar factory.")
parser.add_argument(
    "--speed",
    type=int,
    default=1,
    help='Set execution speed of factory. "One factory second" = "One real second"/EXEC_SPEED',
)
parser.print_help()
args = parser.parse_args()
SPEED = int(args.speed)

# Logging configuration
FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("logger")
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


class InventoryManager:
    """
    The InventoryManager object store ressources of factory : foo, bar, money.
    """

    def __init__(self) -> None:
        # Ressources counter
        self.res_foo = 0
        self.res_bar = 0
        self.res_money = 0
        self.res_foobar = 0

        # Robots
        self.robots_list = []


class Robot:
    """
    Robot makes foo/bar/foobar, sell foobar buy robot.
    """

    counter = itertools.count(1)

    def __init__(self, inventory_manager: "InventoryManager"):
        self._previous_task = RobotTask.NONE
        self._im = inventory_manager
        self.name = f"Robot {next(self.counter)}"

    def _next_task(self):
        res_foo = self._im.res_foo
        res_bar = self._im.res_bar
        res_money = self._im.res_money
        res_foobar = self._im.res_foobar
        logger.info(
            "foo : %s, bar : %s, money : %s, foobar : %s", res_foo, res_bar, res_money, res_foobar
        )  # pylint: disable=line-too-long

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
                    logger.info("%s is moving to new task", self.name)
                    await asyncio.sleep(5 / SPEED)
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
            logger.warning("%s cancelled", self.name)

    async def mining_foo(self):
        """
        Mining foo: takes 1 second.
        """
        logger.info("%s START mining foo", self.name)
        await asyncio.sleep(1 / SPEED)
        self._im.res_foo += 1
        logger.info("%s END mining foo", self.name)

    async def mining_bar(self):
        """
        Mining bar: takes between 0.5 and 2 seconds
        """
        logger.info("%s START mining bar", self.name)
        await asyncio.sleep((random.randint(5, 20) / 10.0) / SPEED)
        self._im.res_bar += 1
        logger.info("%s END mining bar", self.name)

    async def make_foobar(self):
        """
        Making foobar: takes 2 seconds.
        Require 1 foo and 1 bar.
        Success rate : 60%.
        If it fails return bar not foo.
        """
        logger.info("%s START make foobar", self.name)
        await asyncio.sleep(2 / SPEED)

        if self._im.res_foo and self._im.res_bar:
            self._im.res_foo -= 1
            self._im.res_bar -= 1
        else:
            logger.warning("%s Make foobar: ressources unavailable", self.name)
            return

        # success make foobar : 60% chance of success
        if random.randint(1, 10) <= 6:
            # success
            self._im.res_foobar += 1
            logger.info("%s END make foobar: success", self.name)
        else:
            # fail -> Give back bar not foo
            self._im.res_bar += 1
            logger.warning("%s END make foobar: fail", self.name)

    async def sell_foobar(self):
        """
        Sell foobar: takes 10 seconds.
        Robot can sell between 1 to 5 foobar.
        Get 1 money by sold foobar.
        """
        logger.info("%s START sell foobar", self.name)
        await asyncio.sleep(10 / SPEED)

        if self._im.res_foobar:
            nb_foobar_sold = random.randint(1, min(5, self._im.res_foobar))
            self._im.res_money += nb_foobar_sold
            self._im.res_foobar -= nb_foobar_sold
            logger.info("%s END sell %s foobar", self.name, nb_foobar_sold)
        else:
            logger.warning("%s Sell foobar: ressources unavailable", self.name)

    async def buy_robot(self):
        """
        Buy robot: takes not time.
        Cost : 3 money and 6 foo.
        """
        logger.info("%s START buy robot", self.name)
        if self._im.res_money >= 3 and self._im.res_foo >= 6:
            self._im.res_money -= 3
            self._im.res_foo -= 6
        else:
            logger.warning("%s Buy robot : ressources unavailable", self.name)
        logger.info("%s END buy robot", self.name)

        self.create_robot_task()

    def create_robot_task(self):
        """
        Create new robot task: add new coroutine to asyncio loop.
        Terminate factory when 30 robots are runing.
        """
        robot_alive = Robot(self._im)
        self._im.robots_list.append(robot_alive)
        running_loop = asyncio.get_running_loop()
        running_loop.create_task(robot_alive.work(), name=robot_alive.name)

        # Stop runing loop when we have enough robots
        if len(self._im.robots_list) == 30:
            terminate_factory()


def terminate_factory():
    """
    Terminate factory: cancel all runing tasks and stop the loop
    """
    logger.info("The last %s working robots are :", len(asyncio.all_tasks()))
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

# Factory start with 2 robots
for _ in range(2):
    robot = Robot(im)
    im.robots_list.append(robot)
    loop.create_task(robot.work(), name=robot.name)
try:
    loop.run_forever()
except Exception as e:
    logging.error("Exception: %s", e)
    loop.close()
