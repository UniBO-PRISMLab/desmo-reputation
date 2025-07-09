import random
import sys
import numpy as np
import Indexer
import Source
import Oracle
import Blockchain
import enums
import utils
import constants
from tqdm import tqdm
from operator import itemgetter
from argument_parser import apply_arguments_to_constants, parse_args
from EventTimeline import Event, EventTimelineManager

from Source import Producers
from Indexer import Indexers
from Oracle import Oracles
from Blockchain import Blockchains

# Array of Indexer ids ordered by their ranking for printing purposes
ranking = []

# Ranking Master Array
Ranking_avg = []

# Banned Master Array
Banlist = []


# Create new producer, add it to the global list and register it to a random number of indexers
def createAndAssignNewProducer(trusted = True):
    _prod_idx = Source.generateNewProducer(trusted = trusted)

    # TODO the whole part below could be moved to the Indexer class

    interesting_indexers = [] # Let us list only the indexers I want to be enrolled in
    if constants.RATIO_MALICIOUS_INDEXERS > 0 and constants.VERTICAL_ATTACK: # If I am good, then we only select good indexers and vice versa
        interesting_indexers = [i for i in list(Indexers.keys()) if ( Indexers[i].trusted == trusted )]
    if len(interesting_indexers) == 0: # Let us distribute into every indexer if the above condition is not met or the number of indexers is 0
        interesting_indexers = list(Indexers.keys())

    # Long Tail pareto distribution
    #_n_indexers = np.random.randint(1, len(interesting_indexers)) # Register to random number of Indexers
    _n_indexers = min(round(random.paretovariate(alpha=2)), len(interesting_indexers))
    if not _n_indexers > 0:
        print(len(Indexers), " DAMMIT")
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
def runTruthInference(value_matrix, reputation_array, algo=constants.TRUTH_MED):

    result = None

    if algo == constants.TRUTH_AVG:
        result = np.nanmean(value_matrix)

    elif algo == constants.TRUTH_MED:
        result = np.nanmedian(value_matrix)

    elif algo == constants.TRUTH_WAVG:

        # get the dimensions of the value matrix
        n_rows, n_cols = value_matrix.shape
        # extend the reputation array to match the value matrix
        reputation_matrix = np.transpose(np.tile([float(_r) for _r in reputation_array], (n_cols, 1)))
        reputation_matrix += 1 # Make everything positive
        # Normalize the reputation matrix
        reputation_matrix /= np.sum(reputation_matrix)
        result = np.nansum(value_matrix * reputation_matrix)
    elif algo == constants.TRUTH_WMED:
        # get the dimensions of the value matrix
        n_rows, n_cols = value_matrix.shape
        # extend the reputation array to match the value matrix
        reputation_matrix = np.transpose(np.tile([float(_r) for _r in reputation_array], (n_cols, 1)))
        reputation_matrix += 1 # Make everything positive
        # Normalize the reputation matrix
        reputation_matrix /= np.sum(reputation_matrix)
        # Flatten the value matrix and the reputation matrix
        value_matrix_flat = value_matrix.flatten()
        reputation_matrix_flat = reputation_matrix.flatten()

        # Get the indices that would sort the arrays
        sort_indices = np.argsort(value_matrix_flat)

        # Sort the arrays based on the sorted indices
        sorted_values = value_matrix_flat[sort_indices]
        sorted_reputations = reputation_matrix_flat[sort_indices]
        # Calculate the cumulative sum of the reputations
        cumulative_reputations = sorted_reputations.cumsum()
        # Calculate the cutoff as half of the total reputation
        cutoff = sorted_reputations.sum() / 2

        # return the value at the index where the cumulative reputation exceeds the cutoff
        result = sorted_values[cumulative_reputations >= cutoff][0]

    return result if result else 0


def printReputationToFile(dict, filename):
    with open(filename, 'w') as outfile:
        for item in dict.values():
            outfile.write(str(item.reputation)+"\n")

            

if __name__ == "__main__":

    ### Parse the arguments
    args = parse_args()
    apply_arguments_to_constants(args)

    ### Check if we are compromised (i.e. Malicious Oracles and Indexers are taking up MORE than 50% of the value matrix)
    malicious_power = constants.RATIO_MALICIOUS_INDEXERS + constants.RATIO_MALICIOUS_ORACLES - constants.RATIO_MALICIOUS_ORACLES * constants.RATIO_MALICIOUS_INDEXERS
    if malicious_power > 0.5 and constants.SKIP_COMPROMISED:
        sys.exit() # Skip this simulation, there is no point

    ### Initialize the arrival of requests
    for timestamp in utils.generateRequestArray(constants.N_EPOCHS, constants.REQUEST_ARRIVAL_RATE):
        newEvent = Event(timestamp, enums.EventType.Request)
        EventTimelineManager.add_event(newEvent)
    n_total_requests = len(EventTimelineManager.get_timeline())
    if constants._DEBUG_:
        print(f"Generated {n_total_requests} Requests with arrival rate {constants.REQUEST_ARRIVAL_RATE.value}.")

    ### Initialize the Chains
    Blockchain.initiateBlockchains(num_blockchains = constants.B)

    ### Initialize the Oracles
    idx_malicious_oracles = np.random.choice(np.arange(constants.O), int(constants.RATIO_MALICIOUS_ORACLES * constants.O), replace=False)
    for _o in range(constants.O):
        Oracle.generateNewOracle(trusted=(_o not in idx_malicious_oracles))
    if constants._DEBUG_:
        print(f"Generated {len(Oracles)} oracles with {len(idx_malicious_oracles)} malicious ones.")

    ### Initialize the Indexers
    idx_malicious_indexers = np.random.choice(np.arange(constants.I), int(constants.RATIO_MALICIOUS_INDEXERS * constants.I), replace=False)
    for _i in range(constants.I):
        Indexer.generateNewIndexer(trusted=(_i not in idx_malicious_indexers))
    if constants._DEBUG_:
        print(f"Generated {len(Indexers)} indexers with {len(idx_malicious_indexers)} malicious ones.")

    ### Setup the arrival of Producers

    # Number of producers present at cold start and the remainder that will be added during the simulation
    # Note that these are all honest
    P_cold_start = int(constants.P * constants.RATIO_COLD_START)
    P_remainder = constants.P - P_cold_start
    # Fill up the dict of producers and assign each of them to indexers
    for _ in range(P_cold_start):
        createAndAssignNewProducer()
    if constants._DEBUG_:
        print(f"Generated {P_cold_start} honest producers at cold start.")

    # Generate the event timeline for the arrival of producers
    arrivals_timestamps = utils.generateProducersArrivalArray(P_remainder)
    arrivals_malicious_indices = np.random.choice(np.arange(P_remainder), int(constants.RATIO_MALICIOUS_SOURCES * P_remainder), replace=False)
    for i, newProducerTimestamp in enumerate(arrivals_timestamps):
        if i in arrivals_malicious_indices:
            # Generate a malicious producer event
            EventTimelineManager.add_event(Event(newProducerTimestamp, enums.EventType.NewMaliciousProducer))
        else:
            # Generate a benign producer event
            EventTimelineManager.add_event(Event(newProducerTimestamp, enums.EventType.NewHonestProducer))
    if constants._DEBUG_:
        print (f"This simulation will generate {P_remainder} more Producers with {len(arrivals_malicious_indices)} malicious ones.")

    # Shape the arrival of producers depedning on the arrival rate
    if constants.PRODUCERS_ARRIVAL_RATE == enums.ProducerArrival.Uniform:
        pass
    elif constants.PRODUCERS_ARRIVAL_RATE == enums.ProducerArrival.Bursty:
        # Generate a burst of arrivals in the first third of the timeline
        EventTimelineManager.generate_burst(np.random.randint(int(constants.N_EPOCHS / 3.0)) + int(constants.N_EPOCHS / 3.0))
    else:
        print(f"Unknown arrival rate \"{constants.PRODUCERS_ARRIVAL_RATE}\". \nExiting...") 
        sys.exit(0)


    # Set all the counters
    counter_indexers_created = constants.I
    counter_indexers_malign = len(idx_malicious_indexers)
    counter_indexers_banned = 0
    counter_indexers_banned_malign = 0
    counter_sources = P_cold_start
    counter_malign = 0
    counter_banned_sources = 0
    counter_banned_malign = 0
    
    # Number of times the inferred truth is far from the reality
    counter_fail = 0
    counter_tot = 0
    
    # Total event length is the number of events in the timeline plus the responses
    total_event_length = len(EventTimelineManager.get_timeline()) + n_total_requests
    # try:
    print("Algorithm: " + constants.ALGO_LIST[constants.ALGO])

    # EPOCH START
    with open(constants.FILE_OUT, 'w') as outfile, tqdm(total=total_event_length) as tqdm_bar:

        # for epoch in tqdm(range(constants.N_EPOCHS)):
        while len(EventTimelineManager.get_timeline()) > 0:

            # Get the next event
            next_event = EventTimelineManager.get_timeline().pop(0)

            # Update the progress bar
            tqdm_bar.update(1)

            match next_event.type:

                ###### NEW HONEST PRODUCER HANDLING ######
                case enums.EventType.NewHonestProducer:
                    # If it is a new honest producer, we create it and assign it to indexers
                    if constants._DEBUG_:
                        print(f"\n\n////// NEW HONEST PRODUCER at epoch {next_event.timestamp} \\\\\\\\\\\\")
                    createAndAssignNewProducer(trusted=True)
                    counter_sources += 1

                ###### NEW MALICIOUS PRODUCER HANDLING ######   
                case enums.EventType.NewMaliciousProducer:
                    # If it is a new malicious producer, we create it and assign it to indexers
                    if constants._DEBUG_:
                        print(f"\n\n////// NEW MALICIOUS PRODUCER at epoch {next_event.timestamp} \\\\\\\\\\\\")
                    createAndAssignNewProducer(trusted=False)
                    counter_sources += 1
                    counter_malign += 1

                ###### REQUEST HANDLING ######
                case enums.EventType.Request:
                    if constants._DEBUG_:
                        print(f"\n\n////// NEW REQUEST at epoch {next_event.timestamp} \\\\\\\\\\\\")

                    # Pick the best Blockchain to act as a relay
                    relay_chain = Blockchain.selectRelayChain(next_event.timestamp)
                    if constants._DEBUG_:
                        print(f"Selected relay chain: {relay_chain.name} with {len(relay_chain.pending_transactions)} transactions.")

                    # Pick candidate Oracles for the next measurement [selected_oracles is the list of ids]
                    if constants.ALGO == constants.ALGO_AVG:
                        weights = [1.0 for _o in Oracles] # Algo average does not care about the weights nor the ranking
                    else: 
                        weights = [(_o.reputation + 1.0) for _o in Oracles.values()]
                    indices = [_o.idx for _o in Oracles.values()]
                    if len(indices) >= constants.O_req: 
                        selected_oracles = np.random.choice(indices, constants.O_req, p=(weights/np.sum(weights)), replace=False)
                    else:
                        # This happens if there are less oracles than I need so I need to take them all
                        selected_oracles = indices

                    # Pick candidate Indexers for the next measurement
                    indices = list([_i for _i in Indexers.keys() if (len(Indexers[_i].indexed_sources) > 0)]) # Only choose from Indexers with at least one producer
                    if constants.ALGO == constants.ALGO_AVG:
                        weights = [1.0 for _i in indices] # Algo average does not care about the weights nor the ranking
                    else:
                        weights = [(Indexers[_i].reputation + 1.0) for _i in indices]
                    if len(indices) >= constants.S_req: 
                        candidates_indices = np.random.choice(indices, constants.S_req, p=(weights/np.sum(weights)), replace=False)
                    else:
                        # This happens if I kicked out so many indexers that I need to take them all
                        candidates_indices = indices
                    for _i in candidates_indices:
                        Indexers[_i].acceptRequest(next_event.idx) # Record the acceptance of the request for each selected indexer


                    # Select the Producers to query
                    assert len(candidates_indices) <= constants.S_req
                    sources_idx = []
                    sources_indexers_rep = [] # Array of reputation of the indexers respective to the source above
                    for _i in candidates_indices: # Add producers to the list of selectd ones without duplicates
                        _selected_producers_for_indexer = [x for x in Indexers[_i].selectProducers(next_event.idx) if x not in sources_idx]
                        sources_idx.extend(_selected_producers_for_indexer) # With this I take all sources from the candidate indexer
                        sources_indexers_rep.extend(Indexers[_i].reputation for _ in _selected_producers_for_indexer) # For every added producer I also record the reputation of the related indexer
                    
                    # Generate sample for all producers that are indexed by the Candidate Indexes
                    # All producers generate one sample for each querying oracle
                    sources_trusted_idx = [] # This is needed to calculate the truth inference
                    sources_trusted_indexers_rep = [] # Along with the indexers reputation
                    for _i_idx, _i in enumerate(sources_idx):
                        Producers[_i].generateSample(request = next_event.idx, n_samples = len(selected_oracles))
                        # Pick candidates indices for which there is no null value
                        if all(not utils.isNull(_val) for _val in Producers[_i].lastGeneratedSample) or (constants.ALGO == constants.ALGO_AVG):
                            sources_trusted_idx.append(_i)
                            sources_trusted_indexers_rep.append(sources_indexers_rep[_i_idx])

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
                        inferred_truth = runTruthInference(value_matrix, sources_trusted_indexers_rep, algo=constants.TRUTH)
                    else:
                        inferred_truth = np.inf # if everyone gave a nan response
                    if constants._DEBUG_:
                        print(f"----> INFERRED TRUTH: {inferred_truth}")
                    counter_tot += 1
                    if abs(inferred_truth - Source.GROUND_TRUTH) > Source.TOLERANCE: # Check if the query result is compromised
                        counter_fail += 1

                    # Construct the Delay Matrix for calculating the Oracle delays (same shape as value matrix)
                    delay_matrix = np.zeros_like(value_matrix) # first index is the source (row), second index is the oracle (column)
                    for row, _prod in enumerate(delay_matrix):
                        for col, _oracle in enumerate(_prod):
                            del_o = Oracles[selected_oracles[col]].generateDelay()
                            del_p = Producers[sources_trusted_idx[row]].generateDelay() if len(sources_trusted_idx) > 0 else 100.0 # A very high number because it means that there are no producers
                            delay_matrix[row][col] = del_o + del_p
                    delay_array = np.sum(delay_matrix, axis=0)
                    winner = delay_array.min()
                    delay_array -= winner
                    time_threshold = winner / Oracle.SPEED_THRESHOLD_RATIO

                    # Generate a score for each selected producer and update the reputation
                    for _i in sources_idx:
                        Producers[_i].record_score(inferred_truth)
 
                     # Record scores of Indexers
                    for _i in candidates_indices:
                        Indexers[_i].record_score()

                    # Record scores of Oracles - pass in the deviations
                    for _o_id_request, _o in enumerate(selected_oracles):
                        oracle_consistency_array = [Producers[_source].last_consistency_array[_o_id_request] for _source in sources_idx]
                        if len(sources_idx) > 0:
                            Oracles[_o].record_score(
                                # Taking here the scores of all values queried by the oracle (i.e. in position _o_id_request in their score array)
                                oracle_consistency_array,
                                delay_array[_o_id_request],
                                time_threshold
                            )

                    # Generate new Event for the result with the same id as the request 
                    #delay = relay_chain.calculate_delay()
                    response_timestamp = relay_chain.compute_response_timestamp(next_event.timestamp)
                    newEvent = Event(response_timestamp, type = enums.EventType.Result, id = next_event.idx)
                    EventTimelineManager.add_event(newEvent)
                    if constants._DEBUG_:
                        print(f"----> Response timestamp will be at: {newEvent.timestamp} for request {next_event.idx}.")

                    # Add the transaction to the relay chain
                    relay_chain.add_transaction(next_event.idx)
                
                    # Purge the temporary lists - to ensure they are not used in the next iteration
                    del candidates_indices, sources_idx, sources_trusted_idx

                ###### RESULT HANDLING ######
                case enums.EventType.Result:
                    # If it is a result, we need to process the request and update the reputations
                    if constants._DEBUG_:
                        print(f"\n\n////// NEW RESULT at epoch {next_event.timestamp} \\\\\\\\\\\\")

                    # Pop the transaction from the chain
                    Blockchain.resolve_pending_transaction(next_event.idx)

                    # Update the reputation of all producers
                    for _i in Producers.keys():
                        Producers[_i].update_reputation()
                    
                    # Update reputation of all indexers
                    for _i in Indexers.keys():
                        Indexers[_i].update_reputation()

                    # Update reputation of all oracles
                    for _o in Oracles.keys():
                        Oracles[_o].update_reputation()

                    # Kick out the misbehaving indexers
                    if constants.ALGO == constants.ALGO_REP:
                        _items = list(Indexers.values()).copy()
                        for _indexer in _items:
                            if _indexer.reputation < constants.REPUTATION_MIN:
                                Banlist.append(Indexers.pop(_indexer.idx))
                                counter_indexers_banned += 1
                                if not _indexer.trusted:
                                    counter_indexers_banned_malign += 1
                    
                    # Print the ranking
                    if constants._DEBUG_:
                        # printRanking(header="<<<<<< Ranking After Reputation Update >>>>>>", verbose=False, candidates_idx=candidates_indices) # XXX no candidates_indices here
                        printRanking(header="<<<<<< Ranking After Reputation Update >>>>>>", verbose=False)
                        printRanking(header="Banlist:", banned=True)
                        printOracles(header="Oracles:") 

                case _:
                    print(f"Unknown event type: {next_event.type}. Exiting...")
                    sys.exit(0)

            
            #================================#
        
            # Report onto the file

            avg_reputation_benign = ( float(sum([x.reputation for x in (list(Indexers.values()) + Banlist) if x.trusted])) / float(counter_indexers_created - counter_indexers_malign) ) if counter_indexers_created else 0.0
            avg_reputation_malign = ( float(sum([x.reputation for x in (list(Indexers.values()) + Banlist) if not x.trusted])) / float(counter_indexers_malign) ) if counter_indexers_malign else 0.0
            outfile.write(
                ",".join([
                    str(next_event.timestamp),                                     # TIME
                    str(counter_indexers_created),                  # NUMBER OF INDEXERS (active or banned)
                    str(counter_indexers_malign),                   # NUMBER OF MALIGN INDEXERS (active or banned)
                    str(counter_indexers_banned),                   # NUMBER OF INDEXERS (banned)
                    str(counter_indexers_banned_malign),            # NUMBER OF MALIGN INDEXERS (banned)
                    str(inferred_truth),                            # CONSENSUS ACHIEVED
                    str(avg_reputation_benign),                     # AVERAGE REPUTATION OF BENIGN SOURCES
                    str(avg_reputation_malign)                      # AVERAGE REPUTATION OF MALIGN SOURCES
                ]) + "\n"
            )
            
    # EPOCH END
    
    if constants._DEBUG_ and False:
        printProducers(Producers, verbose=True, header="Ranking: ")
        printOracles(Oracles, verbose=True, header="Oracles: ")
        printProducers(Banlist, verbose=True, header="Banlist: ") # Use a different function
    
    printRanking(header="<<<<<< Final Ranking >>>>>>", verbose=False)

    # print(counter_indexers_banned_malign, counter_indexers_banned, counter_indexers_malign)
    print("Precision: {}".format( (counter_indexers_banned_malign / counter_indexers_banned) if counter_indexers_banned else 0 ))
    print("Recall {}".format( (counter_indexers_banned_malign / counter_indexers_malign) if counter_indexers_banned else 0 ))
    print("Ground Truth Accuracy {}".format(1.0 - float(counter_fail) / float(counter_tot)))

    # printReputationToFile(Indexers, "repIndexers.csv")
    # printReputationToFile(Oracles, "repOracles.csv")

    # except Exception as e:
    #     print (e)
    #     os.remove(FILE_OUT)     


