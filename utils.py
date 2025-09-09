import numpy as np
import enums
import constants

# NaN and None are interchangeable for numpy
def isNull(_n):
    return (_n is None) or np.isnan(_n)

# This function transforms the error into a value that ranges from 1 (if the error is 0) and asymptotes to -1 ( if the error is infinite)
def constraintFunction(error, tolerance):
    if isNull(error):
        return -1.0
    else:
        return 2.0 / ( 1.0 + (error / tolerance)**2 ) - 1.0
    

def generateRequestArray(time_interval, arrival_rate = enums.RequestArrival.Medium):
    """
    Generates a list of requests following a Poisson distribution based on the arrival rate.
    - time_interval: The time interval for which to generate requests (in time units).   
    - arrival_rate: The arrival rate of requests (e.g., enums.RequestArrival.Medium).
    """

    if isinstance(arrival_rate, enums.RequestArrival):
        arrival_rate = arrival_rate.value
    else:
        raise ValueError("arrival_rate must be an instance of enums.RequestArrival")
    num_events = np.random.poisson(arrival_rate * time_interval)  # Number of events in the time interval
    inter_event_times = np.random.exponential(1.0 / arrival_rate, num_events)  # array of inter-event times
    event_times = np.cumsum(inter_event_times) # Accumulate to get event times
    return np.round(event_times, 2) # format event_times to have at most two decimal points

def generateProducersArrivalArray(size):
    """
    Generates a list of producers' arrivals following a Uniform distribution in the second third of the timeline.
    - size: The number of producers to generate.
    """
    arrivals = np.random.randint(int(constants.N_EPOCHS / 3.0), high=int(constants.N_EPOCHS / 3.0 * 2.0), size=size)
    arrivals.sort()  # Sort the arrivals to ensure they are in chronological order
    return arrivals.tolist()  # Convert to list for consistency with other functions

def calculateObjectiveFunctionValue(cost, delay):
    """
    Calculates the objective function value based on cost and delay.
    - cost: The cost incurred.
    - delay: The delay experienced.
    """
    if isNull(cost) or isNull(delay):
        return np.nan
    
    cost = (cost / constants.MAX_COST) if cost < constants.MAX_COST else 1.0
    delay = (delay / constants.MAX_TIME) if delay < constants.MAX_TIME else 1.0
    return 1 - (constants.COST_TIME_PARAM * cost + (1 - constants.COST_TIME_PARAM) * delay)