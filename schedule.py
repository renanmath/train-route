from distutils.command.build import build
from event import Event
from terminal import Terminal
from train import Train

class Schedule:
    """
    Model a calendar of events
    """

    def __init__(self, verbose: bool = False) -> None:
        """
        Constructor method
        """

        self.events = list()
        self.events_log = list()
        self.verbose = verbose

    def append_event(self,new_event: Event):
        self.events.append(new_event)
        self.sort_events()

    def pop_event(self) -> Event:
        if len(self.events) > 0:
            event: Event = self.events.pop(0)
            self.events_log.append(event.log_message)
            return event

    
    def sort_events(self):
        self.events.sort(key= lambda ev: ev.begin)

    
    def find_best_time_for_next_event(self, type_next_event:str,
                                            terminal: Terminal, end_last_event:int):

    

        duration = terminal.unload_time if type_next_event == 'unload' else terminal.load_time
        free_time = terminal.free_unload_time if type_next_event == 'unload' else terminal.free_load_time

        scheduled_events = [event for event in self.events
                            if event.terminal.id == terminal.id 
                            and event.type == type_next_event]
        
        scheduled_events.sort(key=lambda ev:ev.begin)


        if len(scheduled_events) == 0:
            return max(end_last_event, free_time)
        
        elif end_last_event + duration < scheduled_events[0].begin:

            return end_last_event
        
        elif len(scheduled_events) == 1:
            return scheduled_events[0].end

        else:

            for i, event in enumerate(scheduled_events[1:]):
                
                prev_event = scheduled_events[i-1]
                if end_last_event >= prev_event.end and end_last_event + duration <= event.begin:
                    begin = end_last_event
                    
                    return begin

                elif prev_event.end + duration <= event.begin:
                    begin = prev_event.end

                    return begin
                else:
                    begin = scheduled_events[-1].end

                    return begin

    
    
    def build_arrival_event(self, prev_event: Event, next_destination: Terminal=None):

        begin = max(prev_event.end, prev_event.terminal.free_recive_time)
        event_description = f'Train {prev_event.train.id} arrived at Terminal {prev_event.destination_terminal.id}'

        next_event = Event(begin=begin, end=begin, type='arrival',
                            description=event_description,
                            train=prev_event.train,
                            terminal=prev_event.destination_terminal)
        
        
        return next_event
    


    def build_unload_event(self, train: Train, terminal: Terminal, end_last_event:int):

        begin = self.find_best_time_for_next_event(type_next_event='unload',
                                                    terminal= terminal,
                                                    end_last_event=end_last_event)

        event_description = f'Train {train.id} is unloading carg at Terminal {terminal.id}'

        end = begin + terminal.unload_time

        next_event = Event(begin=begin, end=end, type='unload',
                            description=event_description, train=train,
                            terminal= terminal)
        return next_event
    
    def build_load_event(self, train: Train, terminal: Terminal, end_last_event:int):

        begin = self.find_best_time_for_next_event(type_next_event='load',
                                                    terminal=terminal,
                                                    end_last_event=end_last_event)

        event_description = f'Train {train.id} is loading carg at Terminal {terminal.id}'

        end = begin + terminal.load_time

        next_event = Event(begin=begin, end=end, type='load',
                            description=event_description, train=train,
                            terminal=terminal)
        return next_event
    
    def build_dispatch_event(self, train: Train, current_terminal: Terminal, next_destination: Terminal, end_last_event:int):

        begin = max(end_last_event, current_terminal.free_dispatch_time)

        event_description = f'Train {train.id} is going from Terminal {current_terminal.id} to Terminal {next_destination.id}'
 
        distance = current_terminal.graph_distances[next_destination.id]
        travel_time = train.calculate_travel_time(distance=distance)
        end = begin + travel_time

        next_event = Event(begin=begin, end=end, type='dispatch',
                            description=event_description, train=train,
                            terminal=current_terminal)

        next_event.destination_terminal = next_destination

        return next_event
        
    
    def schedule_next_event(self, next_destination: Terminal=None) -> Event:
        """
        Schedule a next event, based on info from the last event called.
        Params:
            - next_destination (Terminal): next terminla. Only relevant when scheduling a arrival event.
        """
        
        prev_event = self.pop_event()
        
        if prev_event.type == 'dispatch':
            next_event = self.build_arrival_event(prev_event, next_destination)            


        elif prev_event.type == 'arrival':
            if not prev_event.train.is_empty:
                next_event = self.build_unload_event(train=prev_event.train, 
                                                    terminal=prev_event.terminal,
                                                    end_last_event=prev_event.end)
            else:
                if prev_event.terminal.has_demand:
                    next_event = self.build_load_event(train=prev_event.train,
                                                        terminal=prev_event.terminal,
                                                        end_last_event=prev_event.end)
                else:
                    next_event = self.build_dispatch_event(train=prev_event.train,
                                                        current_terminal=prev_event.terminal,
                                                        next_destination=next_destination,
                                                        end_last_event=prev_event.end)
        
        elif prev_event.type == 'unload':
            if prev_event.terminal.has_demand:
                next_event = self.build_load_event(train=prev_event.train,
                                                        terminal=prev_event.terminal,
                                                        end_last_event=prev_event.end)
            else:
                next_event = self.build_dispatch_event(train=prev_event.train,
                                                        current_terminal=prev_event.terminal,
                                                        next_destination=next_destination,
                                                        end_last_event=prev_event.end)

        
        else:
            next_event = self.build_dispatch_event(train=prev_event.train,
                                                        current_terminal=prev_event.terminal,
                                                        next_destination=next_destination,
                                                        end_last_event=prev_event.end)

        
        next_event.destination_terminal = next_destination
        self.append_event(next_event)
        
        if self.verbose:
            print("-----Schedule event-----")
            print(next_event)
            print("-"*10)
            

        return next_event



