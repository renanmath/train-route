from event import Event
from typing import List
from schedule import Schedule
from train import Train
from terminal import Terminal
from demand import Demand

class Simulator:
    """
    Simulator model
    """

    def __init__(self, trains: List[Train], terminals: List[Terminal], 
                days: int, initial_info: dict, terminals_graph:dict, verbose:bool = False) -> None:
        """
        Constructor method
        Params:
            - trains: list of trains operating
            - terminals: list of terminals operating
            - days (int): total days of simulation
            - initial_info(dict): dictionary with all initial info per train and terminal.
                Structure:
                {
                    'trains':{train_id: {'location': location, 'destination': destination, 'carg': carg}},
                    'terminals': {'terminal_id: {'stock':stock, 'capacity': capacity}}
                }
            - terminals_graph (dict): dictionary with the distances between all connections
            Structure:
            {
                'terminal_id': {connection_id: distance}
            }
        """

        self.trains = trains
        self.termimals = terminals
        self.days = days
        self.initial_info = initial_info
        self.terminals_graph = terminals_graph

        self.time = 0  # instant of time of the simulation, in minutes

        self.stock_per_terminal = {terminal_id: initial_info['terminals'][terminal_id]['stock'] 
                                    for terminal_id in initial_info['terminals']}

        
        for terminal in self.termimals:
            terminal.stock = self.stock_per_terminal[terminal.id]

        self.has_demand_left = any([ter.has_stock for ter in self.termimals])

        self.scheduler = Schedule(verbose=verbose)

        

    
    def get_terminal_from_id(self, terminal_id):
        try:
            return next((terminal for terminal in self.termimals if terminal.id==terminal_id))
        except StopIteration:
            return None

    
    def initiate_simulation(self):

        loading_time = {}
        for terminal in self.termimals:
            terminal.graph_distances = self.terminals_graph[terminal.id]
            loading_time[terminal.id] = 0    
       
        
        for train in self.trains:

            train_id = train.id
            location = self.initial_info['trains'][train_id]['location']
            train.location = location
            terminal = self.get_terminal_from_id(terminal_id=location)
            loading_time[terminal.id] = terminal.load_time           
            
            if train.is_ready:

                destination_terminal_id = initial_info['trains'][train.id]['destination']
                destination_terminal = next((ter for ter in self.termimals if ter.id==destination_terminal_id))

                event = self.scheduler.build_dispatch_event(train=train,
                                                    current_terminal=terminal,
                                                    next_destination=destination_terminal,
                                                    end_last_event=terminal.free_dispatch_time)


                demand = Demand(product='',total=1000,origin=terminal.id,destination=destination_terminal_id)
                train.demand = demand
                
            elif train.is_empty:

                event = self.scheduler.build_load_event(train=train,
                                                        terminal=terminal,
                                                        end_last_event=terminal.free_load_time)               

                destination_terminal_id = initial_info['trains'][train.id]['destination']
                event.destination_terminal = next((ter for ter in self.termimals if ter.id==destination_terminal_id))
                terminal.free_load_time = terminal.free_load_time + terminal.load_time                
            
            else:

                train.is_ready = True
            
            self.scheduler.append_event(event) 
              

    
    def find_best_next_destination(self, current_terminal: Terminal, train: Train, time_horizon:int):
    
        options = [terminal for terminal in self.termimals
                        if terminal != current_terminal 
                        and current_terminal.graph_distances.get(terminal.id, None) is not None]

        
        if current_terminal.has_demand:
            options.sort(key=lambda ter: max(self.time + train.calculate_travel_time(ter.graph_distances[current_terminal.id]), ter.free_unload_time))
        else:
            options.sort(key=lambda ter: max(self.time + train.calculate_travel_time(ter.graph_distances[current_terminal.id]), ter.operation_time))


        best_terminal = options[0]

        return best_terminal


    
    def simulate(self, verbose: bool=False):
      

        time_horizon = self.days*24*60 # maximum time in minutes of the simulation

        self.initiate_simulation()

        while len(self.scheduler.events) > 0 and self.time <= time_horizon:
            
            if not any([ter.has_stock for ter in self.termimals]):
                break
            
            event = self.scheduler.events[0]

            self.time = event.end

            next_destination = self.find_best_next_destination(current_terminal=event.terminal,
                                                            train=event.train,
                                                            time_horizon=time_horizon)
            
            event.callback()             
            
            simulator.scheduler.schedule_next_event(next_destination=next_destination)

        self.scheduler.build_log_sheet()


if __name__ == "__main__":
    terminals_graph = {'1': {'2': 340, '3':340}, '2':{'1':340}, '3':{'1':340}}
    initial_info = {
        'trains': {
            '1':{'location':'1', 'destination':'2', 'carg':1000},
            '2':{'location':'1', 'destination':'3', 'carg':1000},
            '3': {'location':'1', 'destination':'2', 'carg':0}
        },
        'terminals': {
            '1': {'stock': 6000, 'capacity':60000},
            '2': {'stock': 4000, 'capacity':60000},
            '3': {'stock': 0, 'capacity':60000}
        }
    }

    train1 = Train(id='1',velocity_empty=20, velocity_full=17,max_capacity=1000,location='1')
    train1.is_ready = False
    train2 = Train(id='2',velocity_empty=20, velocity_full=17,max_capacity=1000,location='1')
    train2.is_ready = True
    train3 = Train(id='3',velocity_empty=20, velocity_full=17,max_capacity=1000,location='2')
    train3.is_ready = True
    
    

    terminal1 = Terminal(id='1',max_capacity=80000,load_time=420,unload_time=360)
    terminal2 = Terminal(id='2',max_capacity=80000,load_time=420,unload_time=360)
    terminal2.has_demand = True
    terminal3 = Terminal(id='3',max_capacity=80000,load_time=420,unload_time=600)
    terminal3.has_demand = False
    
    days_of_simulation = 30

    simulator = Simulator(trains=[train1, train2], terminals=[terminal1,terminal2, terminal3],
                        days=days_of_simulation,
                        initial_info=initial_info,
                        terminals_graph=terminals_graph,
                        verbose=False)

    
    simulator.simulate()
