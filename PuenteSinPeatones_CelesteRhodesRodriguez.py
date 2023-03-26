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
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.c0 = Value('i', 0)
        self.c1 = Value('i', 0)
        self.turn = Value('i', 0) #0 for c0 ; 1 for c1
        self.c0_waiting = Value('i', 0)
        self.c1_waiting = Value('i', 0)
        self.no_cars0 = Condition(self.mutex)
        self.no_cars1 = Condition(self.mutex)        
        
    def are_no_cars0(self) -> bool:
    	return self.c0.value == 0 and (self.turn.value==1 or self.c0_waiting.value==0)

    def are_no_cars1(self) -> bool:
    	return self.c1.value == 0 and (self.turn.value==0 or self.c1_waiting.value==0)
    	        
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        if direction==0:
            self.c0_waiting.value += 1 
            self.no_cars1.wait_for(self.are_no_cars1)
            self.c0_waiting.value -= 1
            self.c0.value += 1
        elif direction==1:
            self.c1_waiting.value += 1 
            self.no_cars0.wait_for(self.are_no_cars0)
            self.c1_waiting.value -= 1 
            self.c1.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        if direction==0:
            self.c0.value -= 1
            self.turn.value =  1
            if self.c0.value == 0:
                self.no_cars0.notify_all()
                #self.no_cars1.notify_all()
        else:
            self.c1.value -= 1
            self.turn.value = 0
            if self.c1.value == 0:
                self.no_cars1.notify_all()
                #self.no_cars0.notify_all()
        self.mutex.release()



def delay_car_north() -> None:
    time.sleep(1)

def delay_car_south() -> None:
    time.sleep(2)



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


def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gcars.start()
    gcars.join()


if __name__ == '__main__':
    main()
