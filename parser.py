import argparse
from Indexer import Indexer
from Oracle import Oracle
from Source import Source
import constants


def parse_args():
    parser = argparse.ArgumentParser(description="Simulation Configuration")

    parser.add_argument(
        "--reputation_min",
        type=float,
        default=constants.REPUTATION_MIN,
        help="Minimum reputation value before banning an actor",
    )

    parser.add_argument(
        "--ratio_malicious_indexers",
        type=float,
        default=constants.RATIO_MALICIOUS_INDEXERS,
        help="Ratio of malicious indexers",
    )

    parser.add_argument(
        "--alpha", type=float, default=constants.INDEXER_ALPHA, help="Alpha parameter used in reputation updates"
    )

    parser.add_argument(
        "--tolerance", type=float, default=constants.TOLERANCE, help="Tolerance used in truth validation"
    )

    parser.add_argument(
        "--file_out", type=str, default=constants.FILE_OUT, help="Output file name for simulation results"
    )

    parser.add_argument("--algo", type=int, default=constants.ALGO, help="Algorithm selection ID")

    parser.add_argument("--arrival_rate", type=str, default=constants.ARRIVAL_RATE, help="Arrival rate of requests")


    parser.add_argument(
        "--ratio_malicious_oracles",
        type=float,
        default=constants.RATIO_MALICIOUS_ORACLES,
        help="Ratio of malicious oracles",
    )

    parser.add_argument(
        "--truth", type=int, default=constants.TRUTH, help="ID of the truth inference algorithm"
    )

    parser.add_argument(
        "--contract_reads",
        type=int,
        default=constants.CONTRACT_READS,
        help="Number of sequential failed inferences before strategy is declared failed",
    )

    parser.add_argument(
        "--threshold", type=int, default=constants.THRESHOLD, help="Threshold value for detection or filtering"
    )

    parser.add_argument(
        "--farmers_ratio",
        type=float,
        default=constants.FARMERS_RATIO,
        help="Ratio of producers/indexers belonging to farmers",
    )

    parser.add_argument(
        "--insurance_ratio",
        type=float,
        default=constants.INSURANCE_RATIO,
        help="Ratio of producers/indexers belonging to insurance",
    )

    parser.add_argument(
        "--other_ratio",
        type=float,
        default=constants.OTHER_RATIO,
        help="Ratio of producers/indexers belonging to other entities",
    )

    parser.add_argument(
        "--attack_duration",
        type=int,
        default=constants.ATTACK_DURATION,
        help="Duration (in epochs) of the attack phase",
    )

    return parser.parse_args()

def apply_arguments_to_constants(args):
    """
    Applies parsed arguments to constants and relevant class attributes.
    """
    constants.REPUTATION_MIN = args.reputation_min
    constants.RATIO_MALICIOUS_INDEXERS = args.ratio_malicious_indexers
    constants.TOLERANCE = args.tolerance
    constants.FILE_OUT = args.file_out
    constants.ALGO = args.algo
    constants.ARRIVAL_RATE = args.arrival_rate
    constants.RATIO_MALICIOUS_ORACLES = args.ratio_malicious_oracles
    constants.TRUTH = args.truth
    constants.CONTRACT_READS = args.contract_reads
    constants.THRESHOLD = args.threshold
    constants.FARMERS_RATIO = args.farmers_ratio
    constants.INSURANCE_RATIO = args.insurance_ratio
    constants.OTHER_RATIO = args.other_ratio
    constants.ATTACK_DURATION = args.attack_duration

    Indexer.ALPHA = args.alpha
    Source.ALPHA_SOURCE = args.alpha
    Oracle.ALPHA = args.alpha