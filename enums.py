from enum import Enum

# The values specify how many requests per time unit are generated on average
class RequestArrival(float, Enum):
    Slow = 0.02
    Medium = 0.05
    Fast = 0.1

class ProducerArrival(str, Enum):
    Uniform = "uniform" # Malicious producers are uniformly distributed
    Bursty = "bursty" # Malicious producers arrive all at once

# Events that can occur over the timeline
class EventType(str, Enum):
    Request = "request" # A new request arrives and has to be handled
    Result = "result" # A result is returned to the requester, reputations are updated
    NewHonestProducer = "new_honest_producer" # A new producer is added to the system
    NewMaliciousProducer = "new_malicious_producer" # A new malicious producer is added to the system

