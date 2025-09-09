import numpy as np
import enums

# Global variable to assign an ID to Events
event_incremental_idx = 1 

# The global Event Timeline (a list of chronologically ordered events)
EventTimeline = []

class EventTimelineManager:
    """
    This class manages the global Event Timeline, which is a list of chronologically ordered events.
    It provides methods to add new events and retrieve the current timeline.
    """
    
    @staticmethod
    def add_event(event):
        """ Adds a new event to the Event Timeline. """
        EventTimeline.append(event)
        EventTimeline.sort(key=lambda x: x.timestamp)  # Ensure the timeline is sorted by timestamp

    @staticmethod
    def get_timeline():
        """ Returns the current Event Timeline. """
        return EventTimeline
    
    @staticmethod
    def clear_timeline():
        """ Clears the Event Timeline. """
        EventTimeline.clear()

    @staticmethod
    def print_timeline():
        """ Prints the current Event Timeline. """
        for event in EventTimeline:
            event.print_self()

    @staticmethod
    def generate_burst(burst_time):
        """
        Generates a burst of events at a specific time.
        i.e. it changes all timestamp of malicious producer generation to a specific one, so that the attack is bursty.

        :param burst_time: The time at which the burst of events occurs.
        """
        for event in EventTimeline:
            if event.type == enums.EventType.NewMaliciousProducer:
                event.timestamp = burst_time
        EventTimeline.sort(key=lambda x: x.timestamp)


class Event:
    def __init__(self, timestamp, type = enums.EventType.Request, id = 0) -> None:
        """
        Initializes an event with a timestamp and type.
        
        :param timestamp: The time at which the event occurs.
        :param type: The type of the event (default is Request).
        :param id: An optional ID for the event. If 0, an incremental ID is assigned.
        """

        # Assign incremental ID
        global event_incremental_idx
        if id != 0:
            self.idx = id
        else:
            self.idx = event_incremental_idx
            event_incremental_idx += 1

        self.timestamp = timestamp
        self.type = type

    def __repr__(self):
        return f"Event(timestamp={self.timestamp}, type={self.type})"
    def __lt__(self, other):
        """ Less than comparison based on timestamp for sorting. """
        return self.timestamp < other.timestamp
    def __eq__(self, other):
        """ Equality comparison based on timestamp and type. """
        return self.timestamp == other.timestamp and self.type == other.type
    def __hash__(self):
        """ Hash function for the event based on timestamp and type. """
        return hash((self.timestamp, self.type))
    def __str__(self):
        """ String representation of the event. """
        return f"Event at {self.timestamp} of type {self.type.name}"
    def print_self(self):
        """ Prints the event details. """
        print(f"Event at {self.timestamp} of type {self.type.name}")
    def get_timestamp(self):
        """ Returns the timestamp of the event. """
        return self.timestamp
    def get_type(self):
        """ Returns the type of the event. """
        return self.type