import numpy as np
import Source
import utils

from Source import Producers

# How much a new value is important over the history of old values (between 0 and 1)
ALPHA = 0.5

# Initial reputation of a new indexer
INDEXER_REPUTATION_INIT = 0

# How many prouducers should be returned max to reply to a request
MAX_PRODUCERS_REQUEST = 4
POLICY_RANDOM = 0
POLICY_WEIGHTED = 1
POLICY = POLICY_WEIGHTED

# Global variable to assign an ID to Indexers
indexer_incremental_idx = 1

# GLOBAL DICTIONARY OF INDEXERS
Indexers = {}

# Factory
def generateNewIndexer(trusted = True):
    """ Factory method to generate a new Indexer and add it to the Indexers dictionary. """
    _indexer = Indexer(trusted)
    Indexers[_indexer.idx] = _indexer
    return _indexer.idx

class Indexer:

    def __init__(self, trusted = True) -> None:
        
        # Assign incremental ID
        global indexer_incremental_idx
        self.idx = indexer_incremental_idx
        indexer_incremental_idx += 1

        self.trusted = trusted
        self.indexed_sources = []
        self.selected_producers = []
        self.scores = []
        self.last_request = None
        self.reputation = INDEXER_REPUTATION_INIT

    # This function is called if the Indexer is succesfully selected as one of the replier
    def acceptRequest(self, request):
        self.last_request = request

    # Check if indexer indexes a source
    def isIndexed(self, source_id):
        return source_id in self.indexed_sources

    # Register a new source to Indexer (if already registered it has no effect)
    def register(self, source_id: int):
        if not self.isIndexed(source_id):
            self.indexed_sources.append(source_id)

    # Return a list of producers to reply to the current query
    def selectProducers(self, epoch, policy=POLICY):

        num_producers_to_select = min(MAX_PRODUCERS_REQUEST, len(self.indexed_sources))

        if policy == POLICY_RANDOM:
            selected = np.random.choice(self.indexed_sources, num_producers_to_select, replace=False) 
        elif policy == POLICY_WEIGHTED:
            weights = [ (Producers[x].internal_reputation + 1) for x in self.indexed_sources]
            selected = np.random.choice(self.indexed_sources, num_producers_to_select, p=(weights/np.sum(weights)), replace=False)
        else:
            selected = [] # This must never happen

        for _prod_idx in selected:
            Producers[_prod_idx].last_request = epoch

        self.selected_producers = selected
        
        return selected
    
    # Average out the last score of the Sources that replied to the last request
    def record_score(self):
        # Average the scores
        avg_score = 0.0
        scores = 0.0
        for source_id in self.indexed_sources:
            if Producers[source_id].last_request == self.last_request:
                assert not utils.isNull(Producers[source_id].last_score)
                avg_score += Producers[source_id].last_score
                scores += 1
        avg_score = avg_score / scores
        
        # Add to the scores
        self.scores.append(avg_score)
        

    def update_reputation(self):
        for score in self.scores:
            self.reputation = score * ALPHA + self.reputation * (1.0 - ALPHA)
        self.scores = []  # Reset scores after updating reputation


    def print_self(self, verbose=False):
        head = "Trusted" if self.trusted else "Unstrusted"
        if not verbose:
            print("INDEXER " + str(self.idx) + " (" + str(len(self.indexed_sources)) + " prod) - " + head + " - " + str(round(self.reputation * 100, 1)))
        else: 
            print("INDEXER " + str(self.idx) + " (indexing " + str(len(self.indexed_sources)) + " producers) - " + head + " \n\t Reputation: " + str(round(self.reputation * 100, 1))
                 + " \n\t Last Request: " + str(self.last_request)
                 + " \n\t Indexed: " + str(self.indexed_sources)
                 + " \n\t Last Selected: " + str(self.selected_producers)) #str([item for item in self.indexed_sources if (Producers[item].last_request == self.last_request)]))
            for prod_id in self.selected_producers:
                Producers[prod_id].print_self(verbose=verbose)