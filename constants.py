from mode import Mode

_TESTING_ = False
_DEBUG_ = False


MODE = Mode.ZONIA
# ALGORITHMS
ALGO_AVG = 0         # Computes only the average
ALGO_MED = 1         # Computes the median and uses the ranking
ALGO_REP = 2         # Our reputation algorithm
ALGO_LIST = ["Average", "Median + Ranking", "Reputation"]

# Truth inference algorithm
TRUTH_AVG = 0
TRUTH_MED = 1
TRUTH_WAVG = 2
TRUTH_WMED = 3

ALGO = ALGO_REP
TRUTH = TRUTH_WMED

# Total number of oracles
O = 20
if _TESTING_:
    O = 10

# Total number of indexers
I = 20
if _TESTING_:
    I = 20

# Total number of sources
S = 200
if _TESTING_:
    S = 200

# Number of Epochs (the ratio for arrivals is the ratio of epochs in which we add up sources)
N_EPOCHS = 1000
if _TESTING_:
    N_EPOCHS = 60

# Ratio of sources present at cold start (between 0 and 1)
RATIO_COLD_START = 1

# Ratio of malicious Indexers (if there is any, then malicious sources will only go into malicious indexers and good sources into good indexers)
RATIO_MALICIOUS_INDEXERS = 0
VERTICAL_ATTACK = True #Vertical attack forces all malicious sources to go into malicious indexers, otherwise they distribute evenly

# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_SOURCES = RATIO_MALICIOUS_INDEXERS * 2

# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_ORACLES = 0

# This should be one of 'uniform' or 'bursty'
ARRIVAL_RATE = 'bursty'

# Number of oracles chosen for a single request
O_req = 5
if _TESTING_:
    O_req = 4

# Number of indexers chosen for a single request
S_req = 5
if _TESTING_:
    S_req = 3

# Threshold below which a source is banned
REPUTATION_MIN = -0.40

# FILE where to write the results
FILE_OUT = "REP.csv"
GROUND_TRUTH = 17
FALSE_TRUTH = 50

THRESHOLD = 42
# What is the maximum error for a measurement that generates a score of 0 (a higher error value corresponds to a negative score) !CONST
TOLERANCE = 3.0         # Tolerance for the distnace from ground truth


# Initial reputation of a new oracle
ORACLE_REPUTATION_INIT = 0
# How much a new value is important over the history of old values (between 0 and 1)
ORACLE_ALPHA = 0.5
# How much the delay counts in calculating the score versus the consistency 
ORACLE_BETA = 0.25
# This is the maximum speed (minimum avg ms taken for an Oracle to query a Producer)
ORACLE_BASE_SPEED = 125.0
ORACLE_MAX_SPEED_DEVIATION = 4.0
ORACLE_SPEED_VARIANCE = 10.0
# if the fastest oracle takes X, then this number is a number Y such that X/Y is the maximum tolerated delay for oracles
ORACLE_SPEED_THRESHOLD_RATIO = 10.0


# How much a new value is important over the history of old values (between 0 and 1)
INDEXER_ALPHA = 0.5

# Initial reputation of a new indexer
INDEXER_REPUTATION_INIT = 0

# How many prouducers should be returned max to reply to a request
INDEXER_MAX_PRODUCERS_REQUEST = 4
INDEXER_POLICY_RANDOM = 0
INDEXER_POLICY_WEIGHTED = 1
INDEXER_POLICY = INDEXER_POLICY_WEIGHTED



# A defective source sometimes outputs null values
SOURCE_NULLIFY_PROB = 0.05
SOURCE_RATIO_DEFECTIVE = 0.05
SOURCE_DEFECTIVE = False

# Max variance for trusted and untrusted sources for generating their value
# Nullify probability is the probability to yield a null value (defective) for malicious
SOURCE_MAX_VARIANCE = 4.0 # FIXME 4
SOURCE_MAX_VARIANCE_UNTRUSTED = 4.0 # FIXME 12
# Ground truth of the temperature value (we assume always the same) !CONST

SOURCE_DEVIATION_TOL = 1.5     # Tolerance for the consistency
# How much the score (distance from ground truth) is important in the rating versus the consistency. !PARAM
SOURCE_BETA_SOURCE = 0.9
# Number of samples generated for each Source (Oracles)
# This is the default number if not given by externally by the number of oracles.
SOURCE_N_SAMPLES = 4
# How much a new value is important over the history of old values (between 0 and 1)
SOURCE_ALPHA_SOURCE = 0.5
# This is the maximum speed (minimum avg ms taken for a Producer to answer a query)
SOURCE_BASE_SPEED = 125.0
SOURCE_SPEED_VARIANCE = 10.0
# Initial reputation of a new indexer
SOURCE_SOURCE_REPUTATION_INIT = 0

TRUTH_INFERENCE = "greater_equal"
CONTRACT_READS = 5
THRESHOLD = 30

FARMERS_RATIO = 0.5
INSURANCE_RATIO = 0.5
OTHER_RATIO = 0.05
ATTACK_DURATION = 30