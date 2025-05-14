import random
import sys
import numpy as np
import Indexer
import Source
import Oracle
import constants
from mode import Mode
from parser import apply_arguments_to_constants, parse_args
from startegies import chainlink, diorsgx
import use_case
import utils
from tqdm import tqdm

from Source import Producers
from Indexer import Indexers
from truth_inference_checker import truth_inference_checkers
from owner import owners

# Oracles Master Dictionary
Oracles = {}

# Array of Indexer ids ordered by their ranking for printing purposes
ranking = []

# Ranking Master Array
Ranking_avg = []

# Banned Master Array
Banlist = []

truth_checker = truth_inference_checkers[constants.TRUTH_INFERENCE]


# Create new producer, add it to the global list and register it to a random number of indexers
def createNewProducer(trusted=True, owner=0):
    _prod_idx = Source.generateNewProducer(trusted=trusted)

    interesting_indexers = []  # Let us list only the indexers I want to be enrolled in
    if (
        constants.RATIO_MALICIOUS_INDEXERS > 0 and constants.VERTICAL_ATTACK
    ):  # If I am good, then we only select good indexers and vice versa
        interesting_indexers = [i for i in list(Indexers.keys()) if (Indexers[i].trusted == trusted)]
    if len(interesting_indexers) == 0:  # Let us distribute into every indexer
        interesting_indexers = [indexer_key for indexer_key in Indexers if Indexers[indexer_key].owner == owner]

    # Long Tail pareto distribution
    # _n_indexers = np.random.randint(1, len(interesting_indexers)) # Register to random number of Indexers
    _n_indexers = min(round(random.paretovariate(alpha=2)), len(interesting_indexers))
    if not _n_indexers > 0:
        print(len(Indexers), " DAMMIT")
    assert _n_indexers > 0

    for _indexer in np.random.choice(interesting_indexers, _n_indexers, replace=False):  # And pick them randomly
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
        reputation_matrix += 1  # Make everything positive
        # Normalize the reputation matrix
        reputation_matrix /= np.sum(reputation_matrix)
        result = np.nansum(value_matrix * reputation_matrix)

    return result if result else 0


def printReputationToFile(dict, filename):
    with open(filename, "w") as outfile:
        for item in dict.values():
            outfile.write(str(item.reputation) + "\n")


if __name__ == "__main__":
    # Get parameters from ARGV
    args = parse_args()
    apply_arguments_to_constants(args)

    # Number of sources present at cold start and its dual
    S_0 = int(constants.S * constants.RATIO_COLD_START)
    S_remainder = constants.S - S_0

    # @IVAN This shuck of code regulates the arrival rate of the second half of sources over the simulation
    # Array of arrival and of malicious
    arrivals = np.random.randint(
        int(constants.N_EPOCHS / 3.0), high=int(constants.N_EPOCHS / 3.0 * 2.0), size=S_remainder
    )  # FIXME magic numbers
    arrivals.sort()
    arrivals_malicious = np.zeros(S_remainder)
    # Put ones where malicious are
    if constants.ARRIVAL_RATE == "uniform":
        # pick a sample of them with respect to RATIO_MALICIOUS
        for _idx in np.random.choice(
            np.arange(S_remainder), int(constants.RATIO_MALICIOUS_SOURCES * S_remainder), replace=False
        ):
            arrivals_malicious[_idx] = 1.0
    elif constants.ARRIVAL_RATE == "bursty":
        # pick one epoch where the burst takes place and force the next malicious one to happen all at once
        # _burst = np.random.randint(S_remainder - int(RATIO_MALICIOUS_SOURCES * S_remainder) + 1) # XXX OLD BURST happening at the beginning
        _burst = np.random.randint(int(constants.N_EPOCHS / 3.0)) + int(constants.N_EPOCHS / 3.0)
        for _idx in np.random.choice(
            np.arange(S_remainder), int(constants.RATIO_MALICIOUS_SOURCES * S_remainder), replace=False
        ):
            arrivals[_idx] = _burst
        arrivals.sort()
        arrivals_malicious = [1.0 if x == _burst else 0.0 for x in arrivals]

        # for _idx_mal in range(int(RATIO_MALICIOUS_SOURCES * S_remainder)):
        #     arrivals_malicious[_burst + _idx_mal] = 1.0
        #     arrivals[_burst + _idx_mal] = arrivals[_burst]
    else:
        sys.exit(0)

    # Fill up the dict of Oracles
    idx_malicious_oracles = np.random.choice(
        np.arange(constants.O), int(constants.RATIO_MALICIOUS_ORACLES * constants.O), replace=False
    )
    for _o in range(constants.O):
        _oracle = Oracle.Oracle(trusted=(_o not in idx_malicious_oracles))
        Oracles[_oracle.idx] = _oracle

    # Fill up the list of indexers
    idx_malicious_indexers = np.random.choice(
        np.arange(constants.I), int(constants.RATIO_MALICIOUS_INDEXERS * constants.I), replace=False
    )
    counter_indexers_created = constants.I
    counter_indexers_malign = len(idx_malicious_indexers)
    counter_indexers_banned = 0
    counter_indexers_banned_malign = 0
    for owner in owners:
        print(owner)
        for _ in range(owner.number_of_indexers):
            Indexer.generateNewIndexer(trusted=True, owner=owner.identifier)
        for _ in range(owner.number_of_producers):
            createNewProducer(owner=owner.identifier)

    # for _i in range(constants.I):
    #        Indexer.generateNewIndexer(trusted=(_i not in idx_malicious_indexers))

    # @IVAN Create the first batch of sources some of them are malicious?
    # Fill up the dict of sources and assign each of them to indexers
    # for _ in range(S_0):
    #    createNewProducer()

    counter_sources = S_0
    counter_malign = 0
    counter_banned_sources = 0
    counter_banned_malign = 0

    # NUmber of times the inferred truth is far from the reality
    counter_fail = 0
    counter_tot = 0
    counter_sequential_fail = 0

    print("Algorithm: " + constants.ALGO_LIST[constants.ALGO])

    attack_epoch = use_case.define_start_attack_epoch()

    for indexer in Indexers.values():
        if not indexer.trusted:
            raise ValueError("All Indexers should be trusted at epoch 0")
    for source in Producers.values():
        if not source.trusted:
            raise ValueError("All Producers should be trusted at epoch 0")
    # EPOCH START
    with open(constants.FILE_OUT, "w") as outfile:
        fail_counter = 0
        for epoch in tqdm(range(constants.N_EPOCHS)):
            if constants._DEBUG_:
                print(f"\n\n////// EPOCH {epoch} \\\\\\\\\\\\")
            if epoch == attack_epoch:
                print(f" ATTACK EPOCH: {epoch}")
                counter_indexers_malign = use_case.turn_indexers(indexers=list(Indexers.values()))
                print(f"Turned {counter_indexers_malign} indexers into malicious")
            if epoch == attack_epoch + constants.ATTACK_DURATION + 1:
                print(f" ATTACK FINISHED: {epoch}")
                use_case.turn_indexers(indexers=list(Indexers.values()))

            if constants.MODE == Mode.DIORSGX:
                diorsgx.do_DiorSGX(epoch, outfile, truth_checker)
                continue

            elif constants.MODE == Mode.CHAINLINK:
                # select random source
                chainlink.do_chainlink(epoch, outfile, truth_checker)
                continue

            # Pick candidate Oracles for the next measurement [selected_oracles is the list of ids]
            if constants.ALGO == constants.ALGO_AVG:
                weights = [1.0 for _o in Oracles]  # Algo average does not care about the weights nor the ranking
            else:
                weights = [(_o.reputation + 1.0) for _o in Oracles.values()]
            indices = [_o.idx for _o in Oracles.values()]
            if len(indices) >= constants.O_req:
                selected_oracles = np.random.choice(
                    indices, constants.O_req, p=(weights / np.sum(weights)), replace=False
                )
            else:
                # This happens if there are less oracles than .I need so .I need to take them all
                selected_oracles = indices

            # Pick candidate Indexers for the next measurement
            indices = list(
                [_i for _i in Indexers.keys() if (len(Indexers[_i].indexed_sources) > 0)]
            )  # Only choose from Indexers with at least one producer
            if constants.ALGO == constants.ALGO_AVG:
                weights = [1.0 for _i in indices]  # Algo average does not care about the weights nor the ranking
            else:
                weights = [(Indexers[_i].reputation + 1.0) for _i in indices]
            if len(indices) >= constants.S_req:
                candidates_indices = np.random.choice(
                    indices, constants.S_req, p=(weights / np.sum(weights)), replace=False
                )
            else:
                # This happens if I kicked out so many indexers that I need to take them all
                candidates_indices = indices
            for _i in candidates_indices:
                Indexers[_i].acceptRequest(epoch)  # Record the acceptance of the request for each selected indexer

            # Select the Producers to query
            assert len(candidates_indices) <= constants.S_req
            sources_idx = []
            sources_indexers_rep = []  # Array of reputation of the indexers respective to the source above
            for _i in candidates_indices:  # Add producers to the list of selectd ones without duplicates
                _selected_producers_for_indexer = [
                    x for x in Indexers[_i].selectProducers(epoch) if x not in sources_idx
                ]
                sources_idx.extend(
                    _selected_producers_for_indexer
                )  # With this I take all sources from the candidate indexer
                sources_indexers_rep.extend(
                    Indexers[_i].reputation for _ in _selected_producers_for_indexer
                )  # For every added producer I also record the reputation of the related indexer

            # Generate sample for all producers that are indexed by the Candidate Indexes
            # All producers generate one sample for each querying oracle
            sources_trusted_idx = []  # This is needed to calculate the truth inference
            sources_trusted_indexers_rep = []  # Along with the indexers reputation
            for _i_idx, _i in enumerate(sources_idx):
                Producers[_i].generateSample(request=epoch, n_samples=len(selected_oracles))
                # Pick candidates indices for which there is no null value
                if all(not utils.isNull(_val) for _val in Producers[_i].lastGeneratedSample) or (
                    constants.ALGO == constants.ALGO_AVG
                ):
                    sources_trusted_idx.append(_i)
                    sources_trusted_indexers_rep.append(sources_indexers_rep[_i_idx])

            # Make malicious Oracles tamper the values
            for _select_o, _o in enumerate(selected_oracles):
                if not Oracles[_o].trusted:
                    for _i in sources_idx:
                        if Producers[_i].trusted:  # We do not touch untrusted sources
                            # We just project our value to the false truth
                            Producers[_i].lastGeneratedSample[_select_o] -= (
                                constants.GROUND_TRUTH - constants.FALSE_TRUTH
                            )

            # Pick the best value [TRUTH INFERENCE] excluding the defective ones
            if len(sources_trusted_idx) > 0:
                value_matrix = np.array([Producers[_i].lastGeneratedSample for _i in sources_trusted_idx])
                inferred_truth = runTruthInference(value_matrix, sources_trusted_indexers_rep, algo=constants.TRUTH)
                # if epoch >= attack_epoch and epoch <= attack_epoch + constants.ATTACK_DURATION:
                #     print(value_matrix)
            else:
                inferred_truth = np.inf  # if everyone gave a nan response
            if constants._DEBUG_:
                print(f"----> INFERRED TRUTH: {inferred_truth}")
            counter_tot += 1
            if truth_checker(inferred_truth):
                counter_fail += 1
                counter_sequential_fail += 1
            else:
                counter_sequential_fail = 0

            # Construct the Delay Matrix for calcualting the Oracle delays (same shape as value matrix)
            delay_matrix = np.zeros_like(
                value_matrix
            )  # first index is the source (row), second index is the oracle (column)
            for row, _prod in enumerate(delay_matrix):
                for col, _oracle in enumerate(_prod):
                    del_o = Oracles[selected_oracles[col]].generateDelay()
                    del_p = (
                        Producers[sources_trusted_idx[row]].generateDelay() if len(sources_trusted_idx) > 0 else 100.0
                    )  # A very high number because it means that there are no producers
                    delay_matrix[row][col] = del_o + del_p
            delay_array = np.sum(delay_matrix, axis=0)
            winner = delay_array.min()
            delay_array -= winner
            time_threshold = winner / constants.ORACLE_SPEED_THRESHOLD_RATIO

            # Generate a score for each selected producer and update the reputation
            for _i in sources_idx:
                Producers[_i].updateScore(inferred_truth)

            # Update reputation of Indexers
            for _i in candidates_indices:
                Indexers[_i].updateReputation()

            # Update reputation of Oracles ######## PASS IN THE DEVIATIONS
            for _o_id_request, _o in enumerate(selected_oracles):
                oracle_consistency_array = [
                    Producers[_source].last_consistency_array[_o_id_request] for _source in sources_idx
                ]

                if len(sources_idx) > 0:
                    Oracles[_o].updateReputation(
                        # Taking here the scores of all values queried by the oracle (i.e. in position _o_id_request in their score array)
                        oracle_consistency_array,
                        delay_array[_o_id_request],
                        time_threshold,
                    )
                # print(_o, delay_array[_o_id_request], np.mean(oracle_consistency_array))

            # ================================#

            # Kick out the misbehaving

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
                printRanking(
                    header="<<<<<< End of Epoch Ranking >>>>>>", verbose=False, candidates_idx=candidates_indices
                )
                printRanking(header="Banlist:", banned=True)
                printOracles(header="Oracles:")

            # To ensure it is not used anymore and has to be reinitialized
            del candidates_indices
            del sources_idx
            del sources_trusted_idx

            # Report onto the file
            avg_reputation_benign = (
                (
                    float(sum([x.reputation for x in (list(Indexers.values()) + Banlist) if x.trusted]))
                    / float(counter_indexers_created - counter_indexers_malign)
                )
                if counter_indexers_created
                else 0.0
            )
            avg_reputation_malign = (
                (
                    float(sum([x.reputation for x in (list(Indexers.values()) + Banlist) if not x.trusted]))
                    / float(counter_indexers_malign)
                )
                if counter_indexers_malign
                else 0.0
            )
            utils.write_simulation_result(
                outfile=outfile,
                mode_name=Mode.ZONIA,
                epoch=epoch,
                fail_counter=counter_fail,
                consolidated_result=counter_sequential_fail >= constants.CONTRACT_READS,
                counter_indexers_created=counter_indexers_created,
                counter_indexers_malign=counter_indexers_malign,
                counter_indexers_banned=counter_indexers_banned,
                counter_indexers_banned_malign=counter_indexers_banned_malign,
                inferred_truth=inferred_truth,
                avg_reputation_benign=avg_reputation_benign,
                avg_reputation_malign=avg_reputation_malign,
            )
            if epoch >= attack_epoch and epoch <= attack_epoch + constants.ATTACK_DURATION:
                print(f"inferred truth: {inferred_truth}")
            if counter_sequential_fail >= constants.CONTRACT_READS:
                print("FAILED!!!")
                sys.exit(0)

    # EPOCH END

    if constants._DEBUG_ and False:
        printProducers(Producers, verbose=True, header="Ranking: ")
        printOracles(Oracles, verbose=True, header="Oracles: ")
        printProducers(Banlist, verbose=True, header="Banlist: ")  # Use a different function

    printRanking(header="<<<<<< Final Ranking >>>>>>", verbose=False)

    print(counter_indexers_banned_malign, counter_indexers_banned, counter_indexers_malign)
    print(
        "Precision: {}".format(
            (counter_indexers_banned_malign / counter_indexers_banned) if counter_indexers_banned else 0
        )
    )
    print(
        "Recall {}".format(
            (counter_indexers_banned_malign / counter_indexers_malign) if counter_indexers_banned else 0
        )
    )
    if counter_tot > 0:
        print("Ground Truth Accuracy {}".format(1.0 - float(counter_fail) / float(counter_tot)))

    # printReputationToFile(Indexers, "repIndexers.csv")
    # printReputationToFile(Oracles, "repOracles.csv")

    # except Exception as e:
    #     print (e)
    #     os.remove(constants.FILE_OUT)
