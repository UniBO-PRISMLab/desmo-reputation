import numpy as np

from mode import Mode


# NaN and None are interchangeable for numpy
def isNull(_n):
    return (_n is None) or np.isnan(_n)


# This function transforms the error into a value that ranges from 1 (if the error is 0) and asymptotes to -1 ( if the error is infinite)
def constraintFunction(error, tolerance):
    if isNull(error):
        return -1.0
    else:
        return 2.0 / (1.0 + (error / tolerance) ** 2) - 1.0


def write_simulation_result(
    outfile,
    epoch: int,
    mode_name: Mode,
    inferred_truth: int,
    fail_counter: int,
    consolidated_result: bool,
    *,
    counter_indexers_created: int = None,
    counter_indexers_malign: int = None,
    counter_indexers_banned: int = None,
    counter_indexers_banned_malign: int = None,
    avg_reputation_benign: float = None,
    avg_reputation_malign: float = None,
) -> None:
    """
    Writes the simulation result to the specified output file.

    For general modes, it records the epoch, mode, inferred truth, and result validity.
    For ZONIA mode, it includes detailed statistics on indexers and reputations.

    Parameters:
    - outfile: File object opened in write or append mode.
    - epoch (int): The current epoch of the simulation.
    - mode_name (str): Strategy or mode identifier (e.g., "CHAINLINK", "ZONIA").
    - inferred_truth: The inferred truth value (can be numeric or string).
    - consolidated_result (bool, optional): Whether the inferred truth is considered valid.
    - counter_indexers_created (int, optional): Total indexers created (ZONIA only).
    - counter_indexers_malign (int, optional): Malicious indexers created (ZONIA only).
    - counter_indexers_banned (int, optional): Indexers that were banned (ZONIA only).
    - counter_indexers_banned_malign (int, optional): Malicious indexers that were banned (ZONIA only).
    - avg_reputation_benign (float, optional): Avg. reputation of benign sources (ZONIA only).
    - avg_reputation_malign (float, optional): Avg. reputation of malicious sources (ZONIA only).
    """
    if mode_name.value == "ZONIA":
        fields = [
            epoch,
            counter_indexers_created,
            counter_indexers_malign,
            counter_indexers_banned,
            counter_indexers_banned_malign,
            inferred_truth,
            avg_reputation_benign,
            avg_reputation_malign,
            fail_counter,
            consolidated_result,
        ]
    else:
        fields = [
            epoch,
            mode_name.value,
            inferred_truth,
            fail_counter,
            consolidated_result,
        ]

    line = ",".join(str(field) for field in fields) + "\n"
    outfile.write(line)
