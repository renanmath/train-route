from copy import deepcopy
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
                    'terminals': {terminal_id: {'stock':stock, 'capacity': capacity}},
                    'demand': {terminal_id: {other_terminal_id: demand}}

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

        self.time_horizon = self.days*24*60 # maximum time in minutes of the simulation
        
        self.stock_per_terminal = {terminal_id: initial_info['terminals'][terminal_id]['stock'] 

                                    for terminal_id in initial_info['terminals']}


        for train in self.trains:
            train.location = self.initial_info['trains'][train.id]['location']
            train.destination = self.initial_info['trains'][train.id]['destination']
            

        for terminal in self.termimals:
            terminal.graph_distances = self.terminals_graph[terminal.id]
            terminal.stock = self.stock_per_terminal[terminal.id]
        
        
        self.demand_control = [(0, { ter.id : {other_ter_id : 0 for other_ter_id in ter.graph_distances}
                                for ter in self.termimals if ter.has_demand})]

        self.total_operated_demand_per_train = {train.id: 0 for train in self.trains}

        self.total_operated_demand_per_terminal = { ter.id : {other_ter_id : 0 for other_ter_id in ter.graph_distances}
                                for ter in self.termimals if ter.has_demand}

        self.initial_demand = initial_info['demand']
        self.current_demand = initial_info['demand']
        
        self.has_demand_left = any([ter.has_stock for ter in self.termimals])

        self.scheduler = Schedule(verbose=verbose)

        

    
    def get_terminal_from_id(self, terminal_id:str) -> Terminal:
        """
        Returns: terminal object with the given id
        """
        try:
            return next((terminal for terminal in self.termimals if terminal.id==terminal_id))
        except StopIteration:
            return None

    
    def actualize_demand(self, new_demand: Demand, train: Train):
        print("DEBUG atualizar volume")
        print(train.id, train.location, train.destination)

        total = new_demand.total
        origin_id = new_demand.origin
        destination_id = new_demand.destination
        print(total, origin_id, destination_id)

        new_demand_per_terminal = deepcopy(self.demand_control[-1][1])

        new_demand_per_terminal[origin_id][destination_id] += total

        self.demand_control.append((self.time, new_demand_per_terminal))

        self.current_demand[origin_id][destination_id] -= total

        self.total_operated_demand_per_train[train.id] += total

    
    def initiate_simulation(self):
        """
        Initiate all trains and terminals and create the first events
        """

        loading_time = {}
        for terminal in self.termimals:
            terminal.graph_distances = self.terminals_graph[terminal.id]
            loading_time[terminal.id] = 0    
       
        
        for train in self.trains:

            terminal = self.get_terminal_from_id(terminal_id=train.location)
            loading_time[terminal.id] = terminal.load_time

            destination_terminal_id = initial_info['trains'][train.id]['destination']
            destination_terminal = next((ter for ter in self.termimals if ter.id==destination_terminal_id))        
            
            if train.is_ready:

                event = self.scheduler.build_dispatch_event(train=train,
                                                    current_terminal=terminal,
                                                    next_destination=destination_terminal,
                                                    end_last_event=terminal.free_dispatch_time)


                demand = terminal.build_demand_for_train(train=train, product_name='', destination=destination_terminal_id)
                train.demand = demand
                event.demand = demand
                
            elif train.is_empty:

                event = self.scheduler.build_load_event(train=train,
                                                        terminal=terminal,
                                                        next_terminal=destination_terminal,
                                                        end_last_event=terminal.free_load_time)               

                destination_terminal_id = initial_info['trains'][train.id]['destination']
                event.destination_terminal = next((ter for ter in self.termimals if ter.id==destination_terminal_id))
                terminal.free_load_time = terminal.free_load_time + terminal.load_time

                demand = Demand(product='',total=self.initial_info['trains'][train.id]['carg'],origin=terminal.id,destination=destination_terminal_id)
                train.demand = demand
                event.demand = demand   
            
            else:

                train.is_ready = True
            
            self.scheduler.append_event(event) 
              

    
    def check_current_demand_by_terminal(self, current_terminal: Terminal, other_terminal: Terminal):

        if current_terminal.has_demand:
            return self.current_demand[current_terminal.id][other_terminal.id] > 0
        else:
            return True

    
    def find_best_next_destination(self, current_terminal: Terminal, train: Train, end_last_event:int):
        """
        Determinates the best terminal to send the train, given the current conditions of the simulation.
        If the current terminal has demand, train is sent to the terminal minunum free unload time.
        Else, train is sent to the terminal with the minumum free load time or free dispatch time.
        Time travel is also taken in account. 
        """
    
        if train.destination is not None and train.location != 'railroad':
            return self.get_terminal_from_id(terminal_id=train.destination)
        
        options = [terminal for terminal in self.termimals
                        if terminal != current_terminal 
                        and current_terminal.graph_distances.get(terminal.id, None) is not None
                        and self.check_current_demand_by_terminal(current_terminal, terminal)]

        
        if current_terminal.has_demand:
            options.sort(key=lambda ter: max(end_last_event + train.calculate_travel_time(ter.graph_distances[current_terminal.id]), ter.free_unload_time))
        else:
            options.sort(key=lambda ter: max(end_last_event + train.calculate_travel_time(ter.graph_distances[current_terminal.id]), ter.operation_time))


        best_terminal = options[0]

        return best_terminal


    
    def print_statistics(self):
       
        print("*"*20)
        print("Statistics")
        print("Total operated volume per train")
        for train in self.trains:
            print(f"Train {train.id} = {self.total_operated_demand_per_train[train.id]}")

        print("Total volume operated by terminal")

        for terminal in self.demand_control[-1][1]:
            print(f"Terminal {terminal}")
            for other_terminal in self.demand_control[-1][1][terminal]:
                total = self.demand_control[-1][1][terminal][other_terminal]
                print(f"Total volume from {terminal} to {other_terminal} = {total}")

    
    def simulate(self, verbose: bool=False):

        """
        Main simulation loop.
        """

        self.initiate_simulation()

        while len(self.scheduler.events) > 0 and self.time <= self.time_horizon:

            if not any([ter.has_stock and ter.has_demand for ter in self.termimals]):
                print("No stock or demand left")
                break

            event: Event = self.scheduler.events[0] # next event in the schedule

            self.time = event.begin

            next_destination = self.find_best_next_destination(current_terminal=event.terminal,
                                                            train=event.train,
                                                            end_last_event=event.end)
            
            
            if event.demand is not None and event.type == 'dispatch':
                
                self.actualize_demand(new_demand=event.demand, train=event.train)  

            # call event and then schedule the next one
            event.callback()
            
            simulator.scheduler.schedule_next_event(next_destination=next_destination)        

        
        # At the and, create a sheet with the summary of the simulation and print statistics
        self.scheduler.build_log_sheet()

        self.print_statistics()


if __name__ == "__main__":

    terminals_graph = {'1': {'2': 340, '3':340}, '2':{'1':340}, '3':{'1':340}}

    initial_info = {
        'trains': {
            '1':{'location':'1', 'destination':'2', 'carg':1000},
            '2':{'location':'1', 'destination':'3', 'carg':1000},
            '3': {'location':'1', 'destination':'2', 'carg':0}
        },
        'terminals': {
            '1': {'stock': 17000, 'capacity':60000},
            '2': {'stock': 0, 'capacity':60000},
            '3': {'stock': 0, 'capacity':60000}
        },
        'demand': {'1':{'2':14000, '3':3000}, '2':{'1':0}, '3':{'1':0}}
    }

    train1 = Train(id='1',velocity_empty=20, velocity_full=17,max_capacity=1000,location='1')
    train1.is_ready = False
    train2 = Train(id='2',velocity_empty=20, velocity_full=17,max_capacity=1000,location='1')
    train2.is_ready = True
    train3 = Train(id='3',velocity_empty=20, velocity_full=17,max_capacity=1000,location='2')
    train3.is_ready = True
    
    

    terminal1 = Terminal(id='1',max_capacity=80000,load_time=420,unload_time=360)
    terminal2 = Terminal(id='2',max_capacity=80000,load_time=420,unload_time=360)
    terminal2.has_demand = False
    terminal3 = Terminal(id='3',max_capacity=80000,load_time=420,unload_time=600)
    terminal3.has_demand = False
    
    days_of_simulation = 15

    simulator = Simulator(trains=[train1, train2], terminals=[terminal1,terminal2, terminal3],
                        days=days_of_simulation,
                        initial_info=initial_info,
                        terminals_graph=terminals_graph,
                        verbose=False)

    
    simulator.simulate()

    
