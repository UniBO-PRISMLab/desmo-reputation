import random
import sys, os
import numpy as np
import Indexer
import Source
import Oracle
import utils
from tqdm import tqdm
from operator import itemgetter

from Source import Producers
from Indexer import Indexers

_TESTING_ = False
_DEBUG_ = False

# ALGORITHMS
ALGO_AVG = 0         # Computes only the average
ALGO_MED = 1         # Computes the median and uses the ranking
ALGO_REP = 2         # Our reputation algorithm
ALGO_LIST = ["Average", "Median + Ranking", "Reputation"]

ALGO = ALGO_REP

# Total number of oracles
O = 20
if _TESTING_:
    O = 10

# Total number of indexers
I = 100
if _TESTING_:
    I = 10

# Total number of sources
S = 1000 
if _TESTING_:
    S = 1000

# Number of Epochs (the ratio for arrivals is the ratio of epochs in which we add up sources)
N_EPOCHS = 3000
if _TESTING_:
    N_EPOCHS = 60
RATIO_EPOCHS_ARRIVALS = 0.5

# Ratio of sources present at cold start (between 0 and 1)
RATIO_COLD_START = 0.5

# Ratio of malicious Indexers (if there is any, then malicious sources will only go into malicious indexers and good sources into good indexers)
RATIO_MALICIOUS_INDEXERS = 0.3
VERTICAL_ATTACK = True #Vertical attack forces all malicious sources to go into malicious indexers, otherwise they distribute evenly

# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_SOURCES = RATIO_MALICIOUS_INDEXERS * 2



# Ratio of malicious sources within the remaining ones (between 0 and 1)
RATIO_MALICIOUS_ORACLES = 0.0

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

# Oracles Master Dictionary
Oracles = {}

# Array of Indexer ids ordered by their ranking for printing purposes
ranking = []

# Ranking Master Array
Ranking_avg = []

# Banned Master Array
Banlist = []


# Create new producer, add it to the global list and register it to a random number of indexers
def createNewProducer(trusted = True):
    _prod_idx = Source.generateNewProducer(trusted = trusted)

    interesting_indexers = [] # Let us list only the indexers I want to be enrolled in
    if RATIO_MALICIOUS_INDEXERS > 0 and VERTICAL_ATTACK: # If I am good, then we only select good indexers and vice versa
        interesting_indexers = [i for i in list(Indexers.keys()) if ( Indexers[i].trusted == trusted )]
    if len(interesting_indexers) == 0: # Let us distribute into every indexer
        interesting_indexers = list(Indexers.keys())

    # Long Tail pareto distribution
    #_n_indexers = np.random.randint(1, len(interesting_indexers)) # Register to random number of Indexers
    _n_indexers = min(round(random.paretovariate(alpha=2)), len(interesting_indexers))
    assert(_n_indexers > 0)

    for _indexer in np.random.choice(interesting_indexers, _n_indexers, replace=False): # And pick them randomly
        Indexers[_indexer].register(_prod_idx)


def printProducers(_ranking, verbose=False, header="", sources_idx=[]):
    print(header + "\n")
    for r in _ranking.values():
        if r.idx in sources_idx or len(sources_idx) == 0:
            r.print_self(verbose=verbose)

def printOracles(verbose=False, header=""):
    print("\n" + header)
    for r in sorted(Oracles.values(), key=lambda x: x.reputation, reverse=True):
        r.print_self(verbose=verbose)

def printRanking(verbose=False, header="", candidates_idx=[], banned=False):
    print(f"\n{header}")
    if not banned:
        for r in sorted(list(Indexers.values()), key=lambda x: x.reputation, reverse=True):
            if r.idx in candidates_idx or len(candidates_idx) == 0:
                r.print_self(verbose=verbose)
    else:
        for r in Banlist:
            r.print_self(verbose=verbose)

# Find a single value to elect as the Predicted truth.
# Value matrix are the actual values given by the candidates
def runTruthInference(value_matrix, algo=ALGO_REP):
    result = np.nanmedian(value_matrix)
    return result if result else 0

    if (algo == ALGO_AVG):
        result = np.nanmean(value_matrix)
        return result if result else 0

    # PROPOSED ALGORITHM BEGIN
    # FUCK THIS ALGORITHM

    # The matrix of values aligned on time
    sync_matrix = value_matrix # FIXME time processing is missing

    # Autocorrelation: calculate standard deviation of every row (i.e. every candidate) and take the average as best_fluctuation
    # Find the best source that has the closest std to best_fluct
    autocorr = np.std(sync_matrix, axis=1)
    best_fluct = np.mean(autocorr)
    best_source_id = (np.absolute(autocorr - best_fluct)).argmin()

    # Crosscorrelation: calculate standard deviation of every column (i.e. every instant) and take the minimum as best_time
    crosscorr = np.std(sync_matrix, axis=0)
    best_time_id = crosscorr.argmin()

    return value_matrix[best_source_id, best_time_id]

def printReputationToFile(dict, filename):
    with open(filename, 'w') as outfile:
        for item in dict.values():
            outfile.write(str(item.reputation)+"\n")

            

if __name__ == "__main__":

    # Get parameters from ARGV
    
    if len(sys.argv) >= 9:
        # REPUTATION_MIN
        REPUTATION_MIN = float(sys.argv[1])
        # RATIO_MALICIOUS
        RATIO_MALICIOUS_INDEXERS = float(sys.argv[2])
        
        # ALPHA
        Indexer.ALPHA = float(sys.argv[3])
        Source.ALPHA_SOURCE = float(sys.argv[3])
        Oracle.ALPHA = float(sys.argv[3])
        # TOLERANCE
        TOLERANCE = float(sys.argv[4])
        # FILE
        FILE_OUT = sys.argv[5]
        # ALGO
        ALGO = int(sys.argv[6])
        # Arrival Rate
        ARRIVAL_RATE = sys.argv[7]
        # Beta 
        Source.BETA_SOURCE = float(sys.argv[8])
        # Ratio Malicious Oracles
        RATIO_MALICIOUS_ORACLES = float(sys.argv[9])

    # Check if we are compromised (i.e. Malicious Oracles and Indexers are taking up MORE than 50% of the value matrix) FIXME we still try
    # malicious_power = RATIO_MALICIOUS_INDEXERS + RATIO_MALICIOUS_ORACLES - RATIO_MALICIOUS_ORACLES * RATIO_MALICIOUS_INDEXERS
    # if malicious_power > 0.5:
    #     # Skip the simulation, there's no point
    #     sys.exit()

    # Number of sources present at cold start and its dual 
    S_0 = int(S * RATIO_COLD_START)
    S_remainder = S - S_0

    # Array of arrival and of malicious
    # arrivals = np.random.randint(0, high=N_EPOCHS*RATIO_EPOCHS_ARRIVALS, size=S_remainder) OLD ARRIVALS
    arrivals = np.random.randint(int(N_EPOCHS / 3.0), high=int(N_EPOCHS / 3.0 * 2.0), size=S_remainder) # FIXME magic numbers
    arrivals.sort()
    arrivals_malicious = np.zeros(S_remainder)
    # Put ones where malicious are
    if ARRIVAL_RATE == 'uniform':
        # pick a sample of them with respect to RATIO_MALICIOUS
        for _idx in np.random.choice(np.arange(S_remainder), int(RATIO_MALICIOUS_SOURCES * S_remainder), replace=False):
            arrivals_malicious[_idx] = 1.0
    elif ARRIVAL_RATE == 'bursty':
        # pick one epoch where the burst takes place and force the next malicious one to happen all at once
        # _burst = np.random.randint(S_remainder - int(RATIO_MALICIOUS_SOURCES * S_remainder) + 1) # XXX OLD BURST happening at the beginning
        _burst = np.random.randint(int(N_EPOCHS / 3.0)) + int(N_EPOCHS / 3.0)
        for _idx in np.random.choice(np.arange(S_remainder), int(RATIO_MALICIOUS_SOURCES * S_remainder), replace=False):
            arrivals[_idx] = _burst
        arrivals.sort()
        arrivals_malicious = [ 1.0 if x == _burst else 0.0 for x in arrivals ]

        # for _idx_mal in range(int(RATIO_MALICIOUS_SOURCES * S_remainder)):
        #     arrivals_malicious[_burst + _idx_mal] = 1.0
        #     arrivals[_burst + _idx_mal] = arrivals[_burst]
    else:
        sys.exit(0)

    # Fill up the dict of Oracles
    idx_malicious_oracles = np.random.choice(np.arange(O), int(RATIO_MALICIOUS_ORACLES * O), replace=False)
    for _o in range(O):
        _oracle = Oracle.Oracle(trusted=(_o not in idx_malicious_oracles))
        Oracles[_oracle.idx] = _oracle

    # Fill up the list of indexers
    idx_malicious_indexers = np.random.choice(np.arange(I), int(RATIO_MALICIOUS_INDEXERS * I), replace=False)
    counter_indexers_created = I
    counter_indexers_malign = len(idx_malicious_indexers)
    counter_indexers_banned = 0
    counter_indexers_banned_malign = 0
    for _i in range(I):
        Indexer.generateNewIndexer(trusted=(_i not in idx_malicious_indexers))
    
    # Fill up the dict of sources and assign each of them to indexers
    for _ in range(S_0):
        createNewProducer()
       
    counter_sources = S_0
    counter_malign = 0
    counter_banned_sources = 0
    counter_banned_malign = 0
    
    # NUmber of times the inferred truth is far from the reality
    counter_fail = 0
    counter_tot = 0
    
    # try:
    print("Algorithm: " + ALGO_LIST[ALGO])

    # EPOCH START
    with open(FILE_OUT, 'w') as outfile:

        for epoch in tqdm(range(N_EPOCHS)):

            if _DEBUG_:
                print(f"\n\n////// EPOCH {epoch} \\\\\\\\\\\\")

            # Generate new sources if the time has come - evaluate if malicious
            while (len(arrivals) > 0 and epoch == arrivals[0]):
                _trusted = (arrivals_malicious[0] == 0.0) #(np.random.rand() >= RATIO_MALICIOUS)
                
                # Source Creation
                createNewProducer(trusted=_trusted)
                
                arrivals = np.delete(arrivals, 0)
                arrivals_malicious = np.delete(arrivals_malicious, 0)
                counter_sources += 1
                if not _trusted:
                    counter_malign += 1

            # Pick candidate Oracles for the next measurement [selected_oracles is the list of ids]
            if ALGO == ALGO_AVG:
                weights = [1.0 for _o in Oracles] # Algo average does not care about the weights nor the ranking
            else: 
                weights = [(_o.reputation + 1.0) for _o in Oracles.values()]
            indices = [_o.idx for _o in Oracles.values()]
            if len(indices) >= O_req: 
                selected_oracles = np.random.choice(indices, O_req, p=(weights/np.sum(weights)), replace=False)
            else:
                # This happens if there are less oracles than I need so I need to take them all
                selected_oracles = indices

            # Pick candidate Indexers for the next measurement
            indices = list([_i for _i in Indexers.keys() if (len(Indexers[_i].indexed_sources) > 0)]) # Only choose from Indexers with at least one producer
            if ALGO == ALGO_AVG:
                weights = [1.0 for _i in indices] # Algo average does not care about the weights nor the ranking
            else:
                weights = [(Indexers[_i].reputation + 1.0) for _i in indices]
            if len(indices) >= S_req: 
                candidates_indices = np.random.choice(indices, S_req, p=(weights/np.sum(weights)), replace=False)
            else:
                # This happens if I kicked out so many indexers that I need to take them all
                candidates_indices = indices
            for _i in candidates_indices:
                Indexers[_i].acceptRequest(epoch) # Record the acceptance of the request for each selected indexer


            # Select the Producers to query
            assert len(candidates_indices) <= S_req
            sources_idx = []
            for _i in candidates_indices: # Add producers to the list of selectd ones without duplicates
                sources_idx.extend(x for x in Indexers[_i].selectProducers(epoch) if x not in sources_idx) # With this I take all sources from the candidate indexer
            
            # Generate sample for all producers that are indexed by the Candidate Indexes
            # All producers generate one sample for each querying oracle
            sources_trusted_idx = [] # This is needed to calculate the truth inference
            for _i in sources_idx:
                Producers[_i].generateSample(request = epoch, n_samples = len(selected_oracles))
                # Pick candidates indices for which there is no null value
                if all(not utils.isNull(_val) for _val in Producers[_i].lastGeneratedSample) or (ALGO == ALGO_AVG):
                    sources_trusted_idx.append(_i)

            # Make malicious Oracles tamper the values
            for _select_o, _o in enumerate(selected_oracles):
                if not Oracles[_o].trusted:
                    for _i in sources_idx:
                        if Producers[_i].trusted: # We do not touch untrusted sources
                            # We just project our value to the false truth
                            Producers[_i].lastGeneratedSample[_select_o] -= (Source.GROUND_TRUTH - Source.FALSE_TRUTH)


            # Pick the best value [TRUTH INFERENCE] excluding the defective ones
            if len(sources_trusted_idx) > 0:
                value_matrix = np.array([ Producers[_i].lastGeneratedSample for _i in sources_trusted_idx ])
                inferred_truth = runTruthInference(value_matrix, algo=ALGO)
            else:
                inferred_truth = np.inf # if everyone gave a nan response
            if _DEBUG_:
                print(f"----> INFERRED TRUTH: {inferred_truth}")
            counter_tot += 1
            if abs(inferred_truth - Source.GROUND_TRUTH) > Source.TOLERANCE: # Check if the query result is compromised
                counter_fail += 1

            # Construct the Delay Matrix for calcualting the Oracle delays (same shape as value matrix)
            delay_matrix = np.zeros_like(value_matrix) # first index is the source (row), second index is the oracle (column)
            for row, _prod in enumerate(delay_matrix):
                for col, _oracle in enumerate(_prod):
                    delay_matrix[row][col] = Producers[sources_trusted_idx[row]].generateDelay() + Oracles[selected_oracles[col]].generateDelay()
            delay_array = np.sum(delay_matrix, axis=0)
            winner = delay_array.min()
            delay_array -= winner
            time_threshold = winner / Oracle.SPEED_THRESHOLD_RATIO
            
            # Generate a score for each selected producer and update the reputation
            for _i in sources_idx:
                Producers[_i].updateScore(inferred_truth)
                               
            # Update reputation of Indexers
            for _i in candidates_indices:
                Indexers[_i].updateReputation()

            # Update reputation of Oracles ######## PASS IN THE DEVIATIONS
            for _o_id_request, _o in enumerate(selected_oracles):

                oracle_consistency_array = [Producers[_source].last_consistency_array[_o_id_request] for _source in sources_idx]

                Oracles[_o].updateReputation(
                    # Taking here the scores of all values queried by the oracle (i.e. in position _o_id_request in their score array)
                    oracle_consistency_array,
                    delay_array[_o_id_request],
                    time_threshold
                )
                #print(_o, delay_array[_o_id_request], np.mean(oracle_consistency_array))

            #================================#

            # Kick out the misbehaving
            
            if ALGO == ALGO_REP:
                _items = list(Indexers.values()).copy()
                for _indexer in _items:
                    if _indexer.reputation < REPUTATION_MIN:
                        Banlist.append(Indexers.pop(_indexer.idx))
                        counter_indexers_banned += 1
                        if not _indexer.trusted:
                            counter_indexers_banned_malign += 1

            # Print the ranking
            if _DEBUG_:
                printRanking(header="<<<<<< End of Epoch Ranking >>>>>>", verbose=False, candidates_idx=candidates_indices)
                printRanking(header="Banlist:", banned=True)
                printOracles(header="Oracles:") 

            # To ensure it is not used anymore and has to be reinitialized
            del candidates_indices
            del sources_idx
            del sources_trusted_idx

        
            # Report onto the file
            avg_reputation_benign = ( float(sum([x.reputation for x in (list(Indexers.values()) + Banlist) if x.trusted])) / float(counter_indexers_created - counter_indexers_malign) ) if counter_indexers_created else 0.0
            avg_reputation_malign = ( float(sum([x.reputation for x in (list(Indexers.values()) + Banlist) if not x.trusted])) / float(counter_indexers_malign) ) if counter_indexers_malign else 0.0
            outfile.write(
                ",".join([
                    str(epoch),                                      # TIME
                    str(counter_indexers_created),                   # NUMBER OF INDEXERS (active or banned)
                    str(counter_indexers_malign),                    # NUMBER OF MALIGN INDEXERS (active or banned)
                    str(counter_indexers_banned),                      # NUMBER OF INDEXERS (banned)
                    str(counter_indexers_banned_malign),             # NUMBER OF MALIGN INDEXERS (banned)
                    str(inferred_truth),                            # CONSENSUS ACHIEVED
                    str(avg_reputation_benign),                     # AVERAGE REPUTATION OF BENIGN SOURCES
                    str(avg_reputation_malign)                      # AVERAGE REPUTATION OF MALIGN SOURCES
                ]) + "\n"
            )

            print (epoch, avg_reputation_benign, avg_reputation_malign)
            
    # EPOCH END
    
    if _DEBUG_ and False:
        printProducers(Producers, verbose=True, header="Ranking: ")
        printOracles(Oracles, verbose=True, header="Oracles: ")
        printProducers(Banlist, verbose=True, header="Banlist: ") # Use a different function
    
    printRanking(header="<<<<<< Final Ranking >>>>>>", verbose=False)

    print(counter_indexers_banned_malign, counter_indexers_banned, counter_indexers_malign)
    print("Precision: {}".format( (counter_indexers_banned_malign / counter_indexers_banned) if counter_indexers_banned else 0 ))
    print("Recall {}".format( (counter_indexers_banned_malign / counter_indexers_malign) if counter_indexers_banned else 0 ))
    print("Ground Truth Accuracy {}".format(1.0 - float(counter_fail) / float(counter_tot)))

    # printReputationToFile(Indexers, "repIndexers.csv")
    # printReputationToFile(Oracles, "repOracles.csv")

    # except Exception as e:
    #     print (e)
    #     os.remove(FILE_OUT)     


