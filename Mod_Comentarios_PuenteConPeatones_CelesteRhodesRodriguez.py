"""
Solution to the problem: Puente sobre el río Tajuña
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 10 #numero de cochces
NPED = 10 #numero de peatones
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (3, 1) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        """
        Inicialización del monitor.
        
        Args:
            self
        """
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
        """
        Función que comprueba que los coches en dirección 0 pueden pasar, es decir, no hay coches cruzando en dirección 1 ni peatones cruzando.
        
        Args:
            self
        """
        return self.c1.value == 0 and self.ped.value == 0 and (self.turn.value == 0 or (self.c1_waiting.value == 0 and self.ped_waiting.value == 0))
    
    def can_enter_c1(self) -> bool: 
        """
        Función que comprueba que los coches en dirección 1 pueden pasar, es decir, no hay coches cruzando en dirección 0 ni peatones cruzando.
        
        Args:
            self
        """
        return self.c0.value == 0 and self.ped.value == 0 and (self.turn.value == 1 or (self.c0_waiting.value == 0 and self.ped_waiting.value == 0))
    
    def can_enter_ped(self) -> bool: 
        """
        Función que comprueba que los peatones pueden pasar, es decir, no hay coches cruzando en ninguna dirección.
        
        Args:
            self
        """
        return self.c0.value == 0 and self.c1.value == 0 and (self.turn.value == 2 or (self.c0_waiting.value == 0 and self.c1_waiting.value == 0))
    
 
    def wants_enter_car(self, direction: int) -> None:
        """
        El coche quiere cruzar y antes de hacerlo comprueba que puede hacerlo, es decir, que es seguro.
        
        Args:
            self
            direction (int) --> Dirección en la que cruza
        """
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
        """
        El coche acaba de cruzar y avisa a otros procesos de que las condiciones para cruzar pueden haber cambiado.
        
        Args:
            self
            direction (int) --> Dirección en la que cruza
        """
        
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
        """
        El peatón quiere cruzar y antes de hacerlo comprueba que puede hacerlo, es decir, que es seguro.
        
        Args:
            self
        """
        self.mutex.acquire()
        self.ped_waiting.value += 1
        self.enter_ped.wait_for(self.can_enter_ped)
        self.ped_waiting.value -= 1
        self.ped.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        """
        El peatón acaba de cruzar y avisa a otros procesos de que las condiciones para cruzar pueden haber cambiado.
        
        Args:
            self
        """
        self.mutex.acquire()
        self.ped.value -= 1
        self.turn.value = 0
        if self.ped.value == 0:
            self.enter_c0.notify_all()
            self.enter_c1.notify_all()
            self.enter_ped.notify_all()
        self.mutex.release()
        
"""
Funciones que representan el tiempo que tardan en cruzar tanto coches como peatones
"""
        
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
    """
    El coche quiere cruzar el puente en una dirección determinada, solo podrá hacerlo si las condiciones para hacerlo de manera segura se cumplen.
    
    Args:
        cid (int) --> Número de coche
        direction (int) --> Dirección en la que cruza
        monitor (Monitor) --> Monitor
    """
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
    """
    El peaton quiere cruzar el puente, solo podrá hacerlo si las condiciones para hacerlo de manera segura se cumplen.
    
    Args:
        pid (int) --> Número de peatón
        monitor (Monitor) --> Monitor
    """
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    """
    Genera tantos procesos del tipo pedestrian como sea el valor de NPED.

    Args:
        monitor (Monitor) --> Monitor
    """
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
    """
    Genera tantos procesos del tipo car como sea el valor de NCARS.

    Args:
        monitor (Monitor) --> Monitor
    """
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
