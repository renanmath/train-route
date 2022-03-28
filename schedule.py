from distutils.command.build import build
from event import Event
from terminal import Terminal
from train import Train

class Schedule:
    """
    Model a calendar of events
    """

    def __init__(self) -> None:
        """
        Constructor method
        """

        self.events = list()
        self.events_log = list()

    def append_event(self,new_event: Event):
        self.events.append(new_event)
        self.sort_events()

    def pop_event(self) -> Event:
        if len(self.events) > 0:
            event: Event = self.events[0]
            self.events = self.events[1:]
            self.events_log.append(event.log_message)
            return event

    
    def sort_events(self):
        self.events.sort(key= lambda ev: ev.begin)

    
    def find_best_time_for_next_event(self, train: Train, type_next_event:str,
                                            terminal: Terminal, next_terminal: Terminal, time_now:int):

        if type_next_event == 'arrival':

            distance = terminal.graph_distances[next_terminal.id]
            travel_time = train.calculate_travel_time(distance=distance)
            
            begin = next_terminal.free_recive_time
            end = begin

            if train.is_empty:
                if next_terminal.has_demand:
                    increment = next_terminal.load_time
                else:
                    increment = 0
            else:
                increment = next_terminal.unload_time           

            next_terminal.free_recive_time = time_now + travel_time + increment

            return begin, end
            

            

    def find_begin_time_for_next_event(self, prev_event: Event, terminal: Terminal, next_terminal: Terminal) -> int:

        events_cycle = {
            'dispach': 'arrival',
            'arrival': 'unload',
            'unload': 'load',
            'load': 'dispach'
        }
        next_event_type = events_cycle[prev_event.type]
        
        times_setted = [event.begin for event in self.events
                        if event.type ==  next_event_type
                        and event.terminal == prev_event.terminal]
        
        if prev_event.end not in times_setted:
            return prev_event.end
        elif prev_event.type == 'load':
            return prev_event.end + terminal.unload_time
        else:
            return max([event.end for event in self.events
                        if event.type ==  next_event_type
                        and event.terminal == prev_event.terminal])
        

    
    
    def build_arrival_event(self, prev_event: Event, begin:int, next_destination: Terminal=None):
        event_description = f'Train {prev_event.train.id} arrived at Terminal {prev_event.destination_terminal.id}'
        next_event = Event(begin=begin, end=begin, type='arrival',
                            description=event_description,
                            train=prev_event.train,
                            terminal=prev_event.destination_terminal)
        
        next_destination.free_recive_time = max(next_destination.free_recive_time, next_event.end)
        next_destination.free_unload_time = max(next_destination.free_unload_time, next_event.end)
        next_destination.free_load_time = max(next_destination.free_load_time, 
                                            next_destination.free_unload_time+next_destination.unload_time)
        next_destination.free_dispach_time = max(next_destination.free_dispach_time,
                                            next_destination.free_load_time+next_destination.load_time)
        
        return next_event
    


    def build_unload_event(self, prev_event: Event, begin:int, next_destination: Terminal=None):
        event_description = f'Train {prev_event.train.id} is unloading carg at Terminal {prev_event.terminal.id}'
        end = begin + prev_event.terminal.unload_time
        next_event = Event(begin=begin, end=end, type='unload',
                            description=event_description, train=prev_event.train,
                            terminal=prev_event.terminal)
        return next_event
    
    def build_load_event(self, prev_event: Event, begin:int, next_destination: Terminal=None):
        event_description = f'Train {prev_event.train.id} is loading carg at Terminal {prev_event.terminal.id}'
        end = begin+prev_event.terminal.load_time

        next_event = Event(begin=begin, end=end, type='load',
                            description=event_description, train=prev_event.train,
                            terminal=prev_event.terminal)
        return next_event
    
    def build_dispach_event(self, prev_event: Event, begin:int, next_destination: Terminal=None):
        event_description = f'Train {prev_event.train.id} is going from Terminal {prev_event.terminal.id} to Terminal {next_destination.id}'
 
        distance = prev_event.terminal.graph_distances[next_destination.id]
        travel_time = prev_event.train.calculate_travel_time(distance=distance)
        end = begin + travel_time

        next_event = Event(begin=begin, end=end, type='dispach',
                            description=event_description, train=prev_event.train,
                            terminal=prev_event.terminal)
        return next_event
        
    
    def schedule_next_event(self,prev_event: Event, next_destination: Terminal=None) -> Event:
        
        begin = self.find_begin_time_for_next_event(prev_event=prev_event, terminal=prev_event.terminal, next_terminal=next_destination)

        if prev_event.type == 'dispach':
            next_event = self.build_arrival_event(prev_event, begin, next_destination)            


        elif prev_event.type == 'arrival':
            if not prev_event.train.is_empty:
                next_event = self.build_unload_event(prev_event, begin, next_destination)
            else:
                if prev_event.terminal.has_demand:
                    next_event = self.build_load_event(prev_event, begin, next_destination)
                else:
                    next_event = self.build_dispach_event(prev_event, begin, next_destination)
        
        elif prev_event.type == 'unload':
            if prev_event.terminal.has_demand:
                next_event = self.build_load_event(prev_event, begin, next_destination)
            else:
                next_event = self.build_dispach_event(prev_event, begin, next_destination)

        
        elif prev_event.type == 'load':
            next_event = self.build_dispach_event(prev_event, begin, next_destination)
            
        
        else:
            raise ValueError(f"{prev_event.type} is not a valid event")

        
        next_event.destination_terminal = next_destination
        self.append_event(next_event)
        print("-----Schedule event-----")
        print(next_event)
        print("-"*10)  

        return next_event



