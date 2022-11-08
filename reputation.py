import numpy as np
from tqdm import tqdm

_TESTING_ = False
_DEBUG_ = False
source_incremental_idx = 1

# Total number of sources
S = 1000 
if _TESTING_:
    S = 20

# Number of Epochs (the ratio for arrivals is the ratio of epochs in which we add up sources)
N_EPOCHS = 10000
if _TESTING_:
    N_EPOCHS = 20
RATIO_EPOCHS_ARRIVALS = 0.5

# Ratio of sources present at cold start (between 0 and 1)
RATIO_COLD_START = 0.5

# Ratio of sources present at cold start (between 0 and 1)
RATIO_MALICIOUS = 0.3

# Number of sources chosen for a single request
S_req = 10
if _TESTING_:
    S_req = 5

# Initial reputation of a new source
REPUTATION_INIT = 0

# Threshold below which a source is banned
REPUTATION_MIN = -0.40

# Ground truth of the temperature value (we assume always the same)
GROUND_TRUTH = 25
# What is the maximum error for a measurement that generates a score of 0 (a higher error value corresponds to a negative score)
TOLERANCE = 3.0 # Accuracy

# Max variance for trusted and untrusted sources for generating their value
# Nullify probability is the probability to yield a null value (defective) for malicious
MAX_VARIANCE = 4.0
MAX_VARIANCE_UNTRUSTED = 12.0
NULLIFY_PROB = 0.05

# Number of samples generated for each Source
N_SAMPLES = 4

# How much a new value is important over the history of old values (between 0 and 1)
ALPHA = 0.5 # Number of epochs

# FILE where to write the results
FILE_OUT = "REP.csv"

''' 
    Plot1 :
    x- ratio of malicious
    y- how long till i kick them out
    hue - alpha?

    How close the consensus is to the ground truth

    Plot2 : 
    x- ratio of malicious
    y- accuracy malicious/benign
    hue - tolerance?

    Plot3 : 
    x- tempo
    y- reputazione
    hue - malicious/benign

    Simulare bursts di maligni 
        -> solidita del sistema con 50%+ di maligni
'''

# Ranking Master Array
Ranking = []

# Banned Master Array
Banlist = []

def printRanking(_ranking, verbose=False, header=""):
    print(header + "\n")
    for r in _ranking:
        r.print_self(verbose=verbose)

# NaN and None are interchangeable for numpy
def isNull(_n):
    return np.isnan(_n) or (_n is None) 

# This function transforms the difference from the consensus into a value that ranges from 1 (if the error is 0) and asymptotes to -1 ( if the error is infinite)
def calculateScore(error):
    score = 2.0 / ( 1.0 + (error / TOLERANCE)**2 ) - 1.0
    return score

# Find a single value to elect as the Predicted truth.
# Value matrix are the actual values given by the candidates
def runConsensus(value_matrix):

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


class Source:

    def __init__(self, trusted = True):

        global source_incremental_idx
        self.idx = source_incremental_idx
        source_incremental_idx += 1

        self.reputation = REPUTATION_INIT
        self.trusted = trusted
        if trusted:
            self.variance = np.random.rand() * MAX_VARIANCE
        else:
            self.variance = np.random.rand() * MAX_VARIANCE_UNTRUSTED
        self.last_score = None
        self.lastGeneratedSample = None
        return

    # Generate a number of data samples around the ground truth
    # FIXME TIME is not taken into account here
    def generateSample(self):
        self.lastGeneratedSample = np.random.normal(loc=GROUND_TRUTH, scale=self.variance, size=N_SAMPLES)
        # Nullify if unstrusted
        if not self.trusted:
            for _idx, _x in enumerate(self.lastGeneratedSample):
                if np.random.rand() < NULLIFY_PROB:
                    self.lastGeneratedSample[_idx] = None
        return self.lastGeneratedSample

    def updateReputation(self):
        assert not isNull(self.last_score)
        self.reputation = self.last_score * ALPHA + self.reputation * (1 - ALPHA)
        return

    def print_self(self, verbose=False):
        head = "Trusted" if self.trusted else "Unstrusted"
        if not verbose:
            print(str(self.idx) + " - " + head + " - " + str(round(self.reputation * 100, 1)))
        else: 
            print(str(self.idx) + " - " + head + " \n\t Reputation: " + str(round(self.reputation * 100, 1)) + " \n\t Last Sample: " + str(self.lastGeneratedSample) + " \n\t Last Score: " + str(self.last_score))
        return
            

if __name__ == "__main__":

    # Get parameters from ARGV
    
    # REPUTATION_MIN
    # RATIO_MALICIOUS
    # ALPHA
    # TOLERANCE
    # FILE

    # Number of sources present at cold start and its dual 
    S_0 = int(S * RATIO_COLD_START)
    S_remainder = S - S_0

    # Array of arrival
    arrivals = np.random.randint(0, high=N_EPOCHS*RATIO_EPOCHS_ARRIVALS, size=S_remainder)
    arrivals.sort()

    # Fill up the list of sources
    for _i in range(S_remainder):
        Ranking.append(Source(trusted=True))
    counter_sources = S_remainder
    counter_malign = 0
    counter_banned_sources = 0
    counter_banned_malign = 0
    
    # EPOCH START
    with open(FILE_OUT, 'a') as outfile:
        for epoch in tqdm(range(N_EPOCHS)):

            # Generate new sources if the time has come - evaluate if malicious
            while (len(arrivals) > 0 and epoch == arrivals[0]):
                _trusted = (np.random.rand() >= RATIO_MALICIOUS)
                Ranking.append(Source(trusted = _trusted ))
                arrivals = np.delete(arrivals, 0)
                counter_sources += 1
                if not _trusted:
                    counter_malign += 1
                
            # Pick candidates for the next measurement FIXME not fair
            # Maybe exploration vs exploitation? Boltzmann Equation?
            weights = [(_i.reputation + 1.0) for _i in Ranking]
            indices = np.arange(len(Ranking))
            candidates_indices = np.random.choice(indices, S_req, p=(weights/np.sum(weights)), replace=False)

            # Generate sample for each of the Candidates
            assert len(candidates_indices) == S_req
            trusted_indices = []
            for _i in candidates_indices:
                Ranking[_i].generateSample()
                # Pick candidates indices for which there is no null value
                if all(not isNull(_val) for _val in Ranking[_i].lastGeneratedSample):
                    trusted_indices.append(_i)
            

            # Pick the best value [CONSENSUS] excluding the defective ones
            value_matrix = np.matrix([ Ranking[_i].lastGeneratedSample for _i in trusted_indices ])
            consensus = runConsensus(value_matrix)
            if _DEBUG_:
                print("\tCONSENSUS: " + str(consensus))

            # Generate a score for each candidate and update the reputation
            for _i in candidates_indices:
                # If all values are not None
                if _i in trusted_indices:
                    diff_from_consensus = np.min( np.absolute(Ranking[_i].lastGeneratedSample - consensus) )
                    Ranking[_i].last_score = calculateScore(diff_from_consensus)
                else:
                    Ranking[_i].last_score = -1

                # Update reputation
                Ranking[_i].updateReputation()

            # To ensure it is not used anymore and has to be reinitialized
            del candidates_indices 
            del trusted_indices
            
            # Sort the ranking
            Ranking.sort(key=lambda x: x.reputation, reverse=True)

            # Kick out the misbehaving
            for _i, _source in enumerate(Ranking):
                if _source.reputation < REPUTATION_MIN:
                    Banlist.append(Ranking.pop(_i))
                    counter_banned_sources += 1
                    if not _source.trusted:
                        counter_banned_malign += 1
            
           
            # Report onto the file
            avg_reputation_benign = ( float(sum([x.reputation for x in (Ranking + Banlist) if x.trusted])) / float(counter_sources - counter_malign) ) if counter_sources else 0.0
            avg_reputation_malign = ( float(sum([x.reputation for x in (Ranking + Banlist) if not x.trusted])) / float(counter_malign) ) if counter_malign else 0.0
            outfile.write(
                ",".join([
                    str(epoch),                             # TIME
                    str(counter_sources),                   # NUMBER OF SOURCES (active or banned)
                    str(counter_malign),                    # NUMBER OF MALIGN SOURCES (active or banned)
                    str(counter_banned_sources),            # NUMBER OF SOURCES (banned)
                    str(counter_banned_malign),             # NUMBER OF MALIGN SOURCES (banned)
                    str(consensus),                         # CONSENSUS ACHIEVED
                    str(avg_reputation_benign),             # AVERAGE REPUTATION OF BENIGN SOURCES
                    str(avg_reputation_malign)              # AVERAGE REPUTATION OF MALIGN SOURCES
                ]) + "\n"
            )
    # EPOCH END
    
    if _DEBUG_:
        printRanking(Ranking, verbose=True, header="Ranking: ")
        printRanking(Banlist, verbose=True, header="Banlist: ")

    print("Precision: {}".format(counter_banned_malign / counter_banned_sources))
    print("Recall {}".format(counter_banned_malign / counter_malign))
    


