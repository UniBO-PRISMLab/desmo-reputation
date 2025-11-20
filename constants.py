from mode import Mode

_TESTING_ = False
_DEBUG_ = False

INDEXER_REP_FILE = "indexer_rep.py"
FILE_OUT = "ZONIA_Test.csv"

MODE = Mode.ZONIA
# ALGORITHMS
ALGO_AVG = 0         # Computes only the average
ALGO_MED = 1         # Computes the median and uses the ranking
ALGO_REP = 2         # Our reputation algorithm
ALGO_LIST = ["Average", "Median + Ranking", "Reputation"]
FILE_PREFIX = "NWS"
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

NUMBER_OF_SOURCES = 12
NUMBER_OF_MALICIOUS_SOURCES = 0
# Total number of indexers
# I = 8
# if _TESTING_:
#     I = 8

# # Total number of sources
# S = I
# if _TESTING_:
#     S = I


# Ratio of sources present at cold start (between 0 and 1)
RATIO_COLD_START = 1

# Ratio of malicious Indexers (if there is any, then malicious sources will only go into malicious indexers and good sources into good indexers)
VERTICAL_ATTACK = True #Vertical attack forces all malicious sources to go into malicious indexers, otherwise they distribute evenly

# Ratio of malicious sources within the remaining ones (between 0 and 1)

# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_ORACLES = 0

#one message each 5 min
ARRIVAL_RATE_IN_SEC = (1/900)

# Number of oracles chosen for a single request
O_req = 5
if _TESTING_:
    O_req = 4

# Number of indexers chosen for a single request
S_req = 5
if _TESTING_:
    S_req = 3

# Threshold below which a source is banned
REPUTATION_MIN = -20#-0.40

# FILE where to write the results
FALSE_TRUTH = 80

THRESHOLD = 45
# What is the maximum error for a measurement that generates a score of 0 (a higher error value corresponds to a negative score) !CONST
TOLERANCE = 4.0         # Tolerance for the distnace from ground truth


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
THRESHOLD = 50

FARMERS_RATIO = 0.5
INSURANCE_RATIO = 0.5
OTHER_RATIO = 0.05
ATTACK_DURATION_IN_SEC = 3600*4

TRACES_PATH = "./assets/traces"
ATTACKER_VARIANCE = 3.0
DEFAULT_MAX_RECURSION_FOR_TIMESTAMP_SEARCH = 10
MAX_DATA_STALENESS_IN_SEC = 7200