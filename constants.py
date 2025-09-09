import enums

_TESTING_ = False # Set to True for testing parameters
_DEBUG_ = False # Set to True for additional printouts

# Algorithm to perform the selection of nodes
ALGO_LIST = ["Average", "Median + Ranking", "Reputation"]
ALGO_AVG = 0         # Computes only the average
ALGO_MED = 1         # Computes the median and uses the ranking
ALGO_REP = 2         # Our reputation algorithm
ALGO = ALGO_REP

# Truth inference algorithm
TRUTH_AVG = 0 # Computes the average
TRUTH_MED = 1 # Computes the median
TRUTH_WAVG = 2 # Computes the weighted average
TRUTH_WMED = 3 # Computes the weighted median
TRUTH = TRUTH_MED


#Total number of blockchains
B = 3
if _TESTING_:
    B = 3

# Total number of oracles
O = 20
if _TESTING_:
    O = 10

# Total number of indexers
I = 100
if _TESTING_:
    I = 10

# Total number of producers
P = 1000 
if _TESTING_:
    P = 100

# Number of Epochs (the ratio for arrivals is the ratio of epochs in which we add up sources)
N_EPOCHS = 7200 # 2 hours in seconds
if _TESTING_:
    N_EPOCHS = 90

# Ratio of sources present at cold start (between 0 and 1)
RATIO_COLD_START = 0.5

# Ratio of malicious Indexers (if there is any, then malicious sources will only go into malicious indexers and good sources into good indexers)
RATIO_MALICIOUS_INDEXERS = 0.4

#Vertical attack forces all malicious sources to go into malicious indexers, otherwise they distribute evenly
VERTICAL_ATTACK = True

# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_SOURCES = RATIO_MALICIOUS_INDEXERS * 2

# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_ORACLES = 0.0

# Skip the simulation if the number of malicious oracles and indexers is too high
SKIP_COMPROMISED = False

# Producer arrival rate
PRODUCERS_ARRIVAL_RATE = enums.ProducerArrival.Uniform

# The time in which the collusion is active (in seconds)
COLLUSION_TIME = N_EPOCHS / 3.0 * 2.0 

# Request arrival rate
REQUEST_ARRIVAL_RATE = enums.RequestArrival.Medium

# Number of oracles chosen for a single request
O_req = 5
if _TESTING_:
    O_req = 4

# Number of indexers chosen for a single request
S_req = 5
if _TESTING_:
    S_req = 3

# Threshold below which a node is banned
REPUTATION_MIN = -0.40

# How much a new value is important over the history of old values (between 0 and 1)
ALPHA = 0.5

# FILE where to write the results
FILE_OUT = "REP.csv"

# Favourite Chain
# 0 means that the favourite chain is not used, otherwise it is the index of the chain in the list of chains
# -1 means sequential (ideal) which means that the waiting time is always zero
FAV_CHAIN = 0 

# Paramter for the Convex Combination between cost [0] and time [1]
COST_TIME_PARAM = 0.5
MAX_TIME = 30.0 # Maximum time for a request to be answered (in seconds)
MAX_COST = 5000.0 # Maximum cost for a request to be answered (in arbitrary units)