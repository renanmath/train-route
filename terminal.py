from typing import List
from demand import Demand
from train import Train

class Terminal:
    """
    Class to model a terminal
    """

    def __init__(self, id: str, max_capacity: float, load_time: float, unload_time: float) -> None:
        """
        Constructor method
        Params:
            - id (str): unique identification
            - max_capacity (float): maximum capacity of the terminal, in ton
            - load_time (float): time (in min) to load a train
            - unload_time (float): time (in min) to unload a train
            
        """

        self.id = id
        self.max_capacity = max_capacity
        self.stock = 0 # amout of product storeged
        self.capacity = max_capacity  # current capacity
        self.load_time = load_time
        self.unload_time = unload_time

        self.has_demand = True  # flag if the terminal has demand to load

        self.product = None                 # product storaged in terminal
        self.graph_distances = None

        self.current_time = 0

        self.free_load_time = 0
        self.free_unload_time = 0
        self.free_dispatch_time = 0
        self.free_recive_time = 0
    
    
    
    @property
    def has_stock(self):
        return self.stock > 0
    
    @property
    def operation_time(self):
        if self.has_demand:
            return self.free_load_time
        else:
            return self.free_dispatch_time

    def build_demand_for_train(self, train: Train, product_name: str, destination: str):
        
        total_demand = min(train.max_capacity, self.stock)      

        demand = Demand(product=product_name,
                        total=total_demand,
                        origin=self.id,
                        destination=destination)
        

        return demand

    
    def load_train_in_terminal(self, train: Train, destination:str, current_time:int):

        self.current_time = current_time
        demand = self.build_demand_for_train(train=train, 
                                            product_name= self.product,
                                            destination=destination)

        self.capacity -= demand.total
        self.stock -= demand.total
        
        train.load_train(new_demand=demand)
        self.free_load_time = self.current_time + self.load_time
        self.free_dispatch_time = self.free_load_time

        return demand      


    def unload_train_in_terminal(self, train: Train, current_time:int):

        self.current_time = current_time
        self.free_recive_time = self.current_time 
        product, total = train.unload_train()
        self.capacity -= total
        self.product = product
        self.free_unload_time = self.current_time + self.unload_time               

    
    def dispatch_train(self, train: Train, destination: str, current_time:int):
        self.current_time = current_time
        train.location = 'railroad'
        train.destination = destination
        train.arrival_time = current_time + train.calculate_travel_time(distance=self.graph_distances[destination])
        self.free_dispatch_time = current_time
    
    def register_train_arrival(self, train: Train, current_time:int):
        self.current_time = current_time
        train.location = self.id
        train.destination = None
        train.is_ready = False
        self.free_recive_time = current_time


    def __repr__(self) -> str:
        return "Terminal " + self.id   


