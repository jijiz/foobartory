import asyncio
from enum import Enum
import random
import time
import signal

# "One factory second" = "One real second"/EXEC_SPEED
EXEC_SPEED = 1

class RobotTask(Enum):
    NONE = 1
    MINING_FOO = 2
    MINING_BAR = 3
    MAKE_ROBOT = 4
    SELL_ROBOT = 5
    BUY_ROBOT = 6

def log(msg):
    print(f'{time.asctime()} : {msg}')

class InventoryManager():
    """
    The InventoryManager object store ressources of factory : foo, bar, money, robot counter. Store also locks for accessing robot counter and sell action.
    """
    def __init__(self) -> None:
        self.queue_foo = asyncio.Queue()
        self.queue_bar = asyncio.Queue()
        self.queue_money = asyncio.Queue()
        self.queue_foo.put_nowait(1)
        self.queue_bar.put_nowait(1)

        # Unique ID of made robots
        self.robot_counter = 1
        
        # Avoid task to be cancelled more than one time
        self.lock_sell = asyncio.Lock()
        # Maintain consistency of robot counter
        self.lock_robot_counter = asyncio.Lock()

class Robot():
    def __init__(self, inventory_manager :"InventoryManager", name):
        self._previous_task = RobotTask.NONE
        self._im = inventory_manager
        self.name = name

    def _next_task(self):
        foo = self._im.queue_foo.qsize()
        bar = self._im.queue_bar.qsize()
        money = self._im.queue_money.qsize()
        log(f'foo : {foo}, bar : {bar}, money : {money}')

        ListAvailableTask = [RobotTask.MINING_BAR, RobotTask.MINING_FOO]
        # Can robot
        if foo and bar:
            ListAvailableTask.append(RobotTask.MAKE_ROBOT)

        # Can buy robot
        if money >= 3 and foo >= 6:
            ListAvailableTask.append(RobotTask.BUY_ROBOT)

        # Can sell robot
        if self.tasks_len() > 1:
            ListAvailableTask.append(RobotTask.SELL_ROBOT)

        # Return randomly one task from ListAvailableTask
        return ListAvailableTask[random.randint(0,len(ListAvailableTask)-1)]
        
    async def work(self):
        try:
            while True:
                # Choose the next task randomly
                nextTask = self._next_task()

                # Robot moving time
                if (nextTask is not self._previous_task) and (self._previous_task is not RobotTask.NONE):
                    log(f'{self.name} is moving to his next task')
                    await asyncio.sleep(5/EXEC_SPEED)
                self._previous_task = nextTask
                
                # Run the task
                if nextTask is RobotTask.MINING_FOO:
                    await self.mining_foo() 
                elif nextTask is RobotTask.MINING_BAR:
                    await self.mining_bar()
                elif nextTask is RobotTask.MAKE_ROBOT:
                    await self.make_robot()
                elif nextTask is RobotTask.BUY_ROBOT:    
                    await self.buy_robot()
                elif nextTask is RobotTask.SELL_ROBOT:
                    await self.sell_robot()
        except asyncio.CancelledError:
            log(f'{self.name} cancelled')
        else:
            return 1

            
    async def mining_foo(self):
        log(f'{self.name} START mining foo')
        await asyncio.sleep(1/EXEC_SPEED)
        self._im.queue_foo.put_nowait(1)
        log(f'{self.name} END mining foo')

    async def mining_bar(self):
        log(f'{self.name} START mining bar')
        await asyncio.sleep((random.randint(5,20)/10.0)/EXEC_SPEED)
        self._im.queue_bar.put_nowait(1)
        log(f'{self.name} END mining bar')

    async def make_robot(self):
        getOneBar = False
        getOneFoo = False
        try:
            self._im.queue_foo.get_nowait()
            getOneFoo = True
            self._im.queue_bar.get_nowait()
            getOneBar = True

            log(f'{self.name} START make robot')
            await asyncio.sleep(2/EXEC_SPEED)

            # success make robot : 60%
            if random.randint(1,10) <= 6:
                # success
                log(f'{self.name} END make robot')
                await self.create_robot_task()
            else: 
                # fail -> Give back bar not foo
                self._im.queue_bar.put_nowait(1)
                log(f'{self.name} FAILED make robot')
        except asyncio.QueueEmpty as e:
            log(f'{self.name} Failed make robot {e}')
            # Give back bar and foo not consumed
            if getOneFoo:
                self._im.queue_foo.put_nowait(1)
            if getOneBar:
                self._im.queue_bar.put_nowait(1)
            

    async def buy_robot(self):
        await self.create_robot_task()

    async def sell_robot(self):
        log(f'{self.name} START sell robots')
        await asyncio.sleep(10/EXEC_SPEED)
        
        async with self._im.lock_sell:
            tasks = asyncio.all_tasks()
            nbRobotToSell = random.randint(1,min(5, len(tasks)))  
            countSoldRobot = 0

            # could be cleaner
            for task in tasks:
                if task is asyncio.current_task():
                    continue
                else:
                    task.cancel()
                    countSoldRobot+=1
                    log(f'{self.name} sold {task.get_name()}')
                    if countSoldRobot == nbRobotToSell:
                        break

            for i in range(countSoldRobot):
                self._im.queue_money.put_nowait(1)
                   
        log(f'{self.name} END sell robots')


    async def create_robot_task(self):
        robot_alive = Robot(self._im ,name=f'Bob {self._im.robot_counter}')
        loop = asyncio.get_running_loop()
        loop.create_task(robot_alive.work(), name=f'Bob {self._im.robot_counter}')

        async with self._im.lock_robot_counter:
            self._im.robot_counter+=1

        # Stop runing loop when we have enough robots
        if self.tasks_len() == 30:
            terminate_factory()

    def tasks_len(self):
        return len(asyncio.all_tasks())

def terminate_factory():
    log(f'Terminate factory. The last {len(asyncio.all_tasks())} working robots are :')
    for task in asyncio.all_tasks():
        log(f'{task.get_name()}')
        task.cancel()

    asyncio.get_running_loop().stop()

def exit_gracefully(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    terminate_factory()

    # restore the exit gracefully handler    
    signal.signal(signal.SIGINT, exit_gracefully)

# Catch SIGINT to exit gracefully
original_sigint = signal.getsignal(signal.SIGINT)
signal.signal(signal.SIGINT, exit_gracefully)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
inventory_manager = InventoryManager()

robots = [Robot(inventory_manager, name=f'Robot {i}') for i in range(2)]
for robot in robots:
    loop.create_task(robot.work(), name=robot.name)
try:
    loop.run_forever()
except:
    loop.close()