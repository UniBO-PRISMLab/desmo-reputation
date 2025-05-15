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

    If it's the first line of the file, it also writes a header with column names.
    """

    is_first_line = outfile.tell() == 0

    if mode_name.value == Mode.ZONIA:
        headers = [
            "epoch",
            "indexers_created",
            "indexers_malign",
            "indexers_banned",
            "indexers_banned_malign",
            "inferred_truth",
            "avg_rep_benign",
            "avg_rep_malign",
            "mode",
            "fail_counter",
            "consolidated_result",
        ]
        fields = [
            epoch,
            counter_indexers_created,
            counter_indexers_malign,
            counter_indexers_banned,
            counter_indexers_banned_malign,
            inferred_truth,
            avg_reputation_benign,
            avg_reputation_malign,
            mode_name.value,
            fail_counter,
            consolidated_result,
        ]
    else:
        headers = [
            "epoch",
            "mode",
            "inferred_truth",
            "fail_counter",
            "consolidated_result",
        ]
        fields = [
            epoch,
            mode_name.value,
            inferred_truth,
            fail_counter,
            consolidated_result,
        ]

    if is_first_line:
        outfile.write(",".join(headers) + "\n")

    outfile.write(",".join(str(field) for field in fields) + "\n")
