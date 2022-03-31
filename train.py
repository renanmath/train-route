import imp
from demand import Demand

class Train:
    """
    Class to model a train
    """

    def __init__(self, id: str, velocity_empty: float, 
    velocity_full:float, max_capacity:float, location:str = None, demand: Demand=None) -> None:
        """
        Constructor method
        Params:
            - id (str): unique identification
            - velocity_empty (float): mean velocity of the train with no carg, in km/h
            - velocity_empty (float): mean velocity of the train with full carg, in km/h
            - max_capacity (float): maximum capacity of the train, in tons
            - location: id of terminal where train is currently locate or railroad
            - demand (Demand): objet of info of the carg of the train
        """

        self.id = id
        self.velocity_empty = velocity_empty
        self.velocity_full = velocity_full
        self.max_capacity = max_capacity

        self.capacity = max_capacity # current capacity
        self.demand = demand
        self.location = location
        self.destination = None

        self.arrival_time: int = 0  # time the train will arrive at the next terminal
        self.travel_time = None   # time in minutes to complete the travel from on terminmal to another
        self.is_ready = False

    
    @property
    def is_empty(self):
        return self.demand is None
    
    def load_train(self, new_demand: Demand):
        """
        Load the train with a new demand
        """
        if self.is_empty:        
            self.demand = new_demand
            self.capacity = self.max_capacity - new_demand.total
            self.destination = new_demand.destination
            self.is_ready = True

    def unload_train(self):
        """
        Unload the train
        Return: tuple with product and total
        """

        if not self.is_empty:
            product = self.demand.product
            total = self.demand.total

            self.capacity += total
            self.demand = None

            return product,total
        else:
            return None, None

    def calculate_travel_time(self, distance: float):
        if self.is_empty:
            self.travel_time = int(60*distance/self.velocity_empty)
        else:
            self.travel_time = int(60*distance/self.velocity_full)
        
        return self.travel_time

    

    def __repr__(self) -> str:
        return 'Train ' + self.id
