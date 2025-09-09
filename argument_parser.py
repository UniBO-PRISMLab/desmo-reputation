import argparse
import Indexer
import Oracle
import Source
import constants


def parse_args():
    parser = argparse.ArgumentParser(description="Simulation Configuration")

    parser.add_argument(
        "--reputation_min",
        type=float,
        default=constants.REPUTATION_MIN,
        help="Minimum reputation value before banning a node",
    )

    parser.add_argument(
        "--ratio_malicious_indexers",
        type=float,
        default=constants.RATIO_MALICIOUS_INDEXERS,
        help="Ratio of malicious indexers",
    )

    parser.add_argument(
        "--alpha", type=float, default=constants.ALPHA, help="How much a new value is important over the history of old values (between 0 and 1)"
    )

    parser.add_argument(
        "--tolerance", type=float, default=Source.TOLERANCE, help="Tolerance used in truth validation with continuous values"
    )

    parser.add_argument(
        "--file_out", type=str, default=constants.FILE_OUT, help="Output file name for simulation results"
    )

    parser.add_argument(
        "--algo", type=int, default=constants.ALGO, help="Algorithm for the selection of nodes"
    )

    parser.add_argument(
        "--arrival_rate", type=str, default=constants.PRODUCERS_ARRIVAL_RATE.value, help="Arrival rate of malicious producers"
    )

    parser.add_argument(
        "--ratio_malicious_oracles",
        type=float,
        default=constants.RATIO_MALICIOUS_ORACLES,
        help="Ratio of malicious oracles",
    )

    parser.add_argument(
        "--truth", type=int, default=constants.TRUTH, help="Truth inference algorithm"
    )

    parser.add_argument(
        "--blockchain_num",
        type=int,
        default=constants.B,
        help="Number of blockchains to use in the simulation",
    )

    parser.add_argument(
        "--fav_chain",
        type=int,
        default=constants.FAV_CHAIN,
        help="Index of the favourite chain (-1 means no favourite chain and the selection is automatic)",
    )


    parser.add_argument(
        "--cost-time-param",
        type=float,
        default=constants.COST_TIME_PARAM,
        help="Parameter for the convex combination between cost and time (between 0 and 1)",
    )

    return parser.parse_args()

def apply_arguments_to_constants(args):
    """
    Applies parsed arguments to constants and relevant class attributes.
    """
    constants.REPUTATION_MIN = args.reputation_min
    constants.RATIO_MALICIOUS_INDEXERS = args.ratio_malicious_indexers
    Source.TOLERANCE = args.tolerance
    constants.FILE_OUT = args.file_out
    constants.ALGO = args.algo
    constants.PRODUCERS_ARRIVAL_RATE = args.arrival_rate
    constants.RATIO_MALICIOUS_ORACLES = args.ratio_malicious_oracles
    constants.TRUTH = args.truth
    constants.B = args.blockchain_num
    constants.FAV_CHAIN = args.fav_chain
    constants.COST_TIME_PARAM = args.cost_time_param

    Indexer.ALPHA = args.alpha
    Source.ALPHA_SOURCE = args.alpha
    Oracle.ALPHA = args.alpha