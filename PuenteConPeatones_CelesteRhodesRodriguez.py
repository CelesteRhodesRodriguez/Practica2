"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 10
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (3, 1) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.c0 = Value('i', 0)
        self.c1 = Value('i', 0)
        self.ped = Value('i', 0)
        self.c0_waiting = Value('i', 0)
        self.c1_waiting = Value('i', 0)
        self.ped_waiting = Value('i', 0)
        self.turn = Value('i', 0) #-1 no one ; 0 for c0 ; 1 for c1 ; 2 for ped
        self.enter_c0 = Condition(self.mutex)
        self.enter_c1 = Condition(self.mutex)
        self.enter_ped = Condition(self.mutex)
             

    def can_enter_c0(self) -> bool: 
        return self.c1.value == 0 and self.ped.value == 0 and (self.turn.value == 0 or (self.c1_waiting.value == 0 and self.ped_waiting.value == 0))
    
    def can_enter_c1(self) -> bool: 
        return self.c0.value == 0 and self.ped.value == 0 and (self.turn.value == 1 or (self.c0_waiting.value == 0 and self.ped_waiting.value == 0))
    
    def can_enter_ped(self) -> bool: 
        return self.c0.value == 0 and self.c1.value == 0 and (self.turn.value == 2 or (self.c0_waiting.value == 0 and self.c1_waiting.value == 0))
    
 
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        if direction==0:
            self.c0_waiting.value += 1 
            self.enter_c0.wait_for(self.can_enter_c0)
            self.c0_waiting.value -= 1
            self.c0.value += 1
        elif direction==1:
            self.c1_waiting.value += 1 
            self.enter_c1.wait_for(self.can_enter_c1)
            self.c1_waiting.value -= 1 
            self.c1.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        if direction==0:
            self.c0.value -= 1
            self.turn.value =  1
            if self.c0.value == 0:
                self.enter_c0.notify_all()
                self.enter_c1.notify_all()
                self.enter_ped.notify_all()
        else:
            self.c1.value -= 1
            self.turn.value = 2
            if self.c1.value == 0:
                self.enter_c0.notify_all()
                self.enter_c1.notify_all()
                self.enter_ped.notify_all()
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.ped_waiting.value += 1
        self.enter_ped.wait_for(self.can_enter_ped)
        self.ped_waiting.value -= 1
        self.ped.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.ped.value -= 1
        self.turn.value = 0
        if self.ped.value == 0:
            self.enter_c0.notify_all()
            self.enter_c1.notify_all()
            self.enter_ped.notify_all()
        self.mutex.release()
        
        
def delay_car_north() -> None:
    delay=random.uniform(TIME_IN_BRIDGE_CARS[0], TIME_IN_BRIDGE_CARS[1])
    time.sleep(delay)
    
def delay_car_south() -> None:
    delay=random.uniform(TIME_IN_BRIDGE_CARS[0], TIME_IN_BRIDGE_CARS[1])
    time.sleep(delay)
    
def delay_pedestrian() -> None:
    delay=random.uniform(TIME_IN_BRIDGE_PEDESTRIAN[0],TIME_IN_BRIDGE_PEDESTRIAN[1])
    time.sleep(delay)


def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter.")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge.")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge.")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge.")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()


def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()



if __name__ == '__main__':
    main()
