import math
from typing import Callable, Optional
from demand import Demand
from train import Train
from terminal import Terminal

class Event:
    """
    Model a event of the simulation
    """

    def __init__(self, begin: int, end: int, type: str, description: str = None, 
                train: Train = None, terminal: Terminal = None, demand: Demand = None ) -> None:
        """
        Constructor method
        Params:
            - description (str): description of the event
            - callback: function to be called when event starts
            - train: train
            - terminal: terminal
            - demand: demand
        """

        if type.lower() not in ['dispatch', 'arrival', 'unload', 'load']:
            raise EventException(f"{type} is not a valid type of event")

        self.begin = begin
        self.end = end
        self.description = description
        self.type = type
        self.train = train
        self.terminal = terminal
        self.demand = demand

        self.destination_terminal: Optional[Terminal] = None

        if self.description is not None:
            self.log_message = "On " + self.convert_minutes_to_date(minutes=self.begin)[0] + "---> " + self.description
        else:
            self.log_message = "On " + self.convert_minutes_to_date(minutes=self.begin)[0] + "---> " + f"Event {self.type}"
 


    def load_train_in_terminal(self):
        demand = self.terminal.load_train_in_terminal(train=self.train, 
                                            destination=self.destination_terminal.id,
                                            current_time=self.begin)
        self.demand = demand

    def unload_train_in_terminal(self):
        self.terminal.unload_train_in_terminal(train=self.train, current_time=self.begin)

    def dispatch_train_from_terminal(self):
        self.terminal.dispatch_train(train=self.train,
                                    destination=self.destination_terminal.id,
                                    current_time=self.begin)
    
    def train_arrives_at_terminal(self):
        self.terminal.register_train_arrival(train=self.train, current_time=self.begin)


    
    def callback(self):

        print(self.log_message)
        if self.type == 'load':
            self.load_train_in_terminal()
        elif self.type == 'unload':
            self.unload_train_in_terminal()
        elif self.type == 'dispatch':
            self.dispatch_train_from_terminal()
        elif self.type == 'arrival':
            self.train_arrives_at_terminal()
        else:
            raise ValueError(f"{self.type} is not a valid event")



    def __repr__(self) -> str:
        return "Event " + self.type + "\n" + self.description +"\n" + self.convert_minutes_to_date(self.begin)[0] + "---" + self.convert_minutes_to_date(self.end)

    
    @staticmethod
    def convert_minutes_to_date(minutes: int):
        day = math.floor(minutes/(24*60)) + 1
        remaining = minutes - 60*24*(day-1)
        hour = math.floor(remaining/60)
        minu = remaining - hour*60

        digit1 = "0"*(len(str(day))==1)
        digit2 = "0"*(len(str(hour))==1)
        digit3 = "0"*(len(str(minu))==1)

        text = f"Day {digit1}{day}, {digit2}{hour}H:{digit3}{minu}m"

        return text, f"{digit1}{day}", f"{digit2}{hour}H:{digit3}{minu}m"

    @property
    def info(self):

        info = {
            'type': self.type,
            'begin': self.begin,
            'end': self.end,
            'begin_day': self.convert_minutes_to_date(self.begin)[1],
            'begin_hour': self.convert_minutes_to_date(self.begin)[2],
            'end_day': self.convert_minutes_to_date(self.end)[1],
            'end_hour': self.convert_minutes_to_date(self.begin)[2],
            'train': self.train.id,
            'terminal': self.terminal.id,

        }

        return info


class EventException(Exception):
    pass


