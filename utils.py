import numpy as np
import os
import random
import pandas as pd

from datetime import datetime
from typing import Optional, List

import constants
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


def count_lines_after_timestamp(timestamp_str: str, file_path: str) -> int:
    """
    Counts the number of lines in a CSV file that have a timestamp strictly
    greater than the given timestamp_str.
    """
    target_dt = pd.to_datetime(timestamp_str, format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce")       
    df_time_col = pd.read_csv(file_path, usecols=["time"])
    times_series = pd.to_datetime(df_time_col["time"], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce")       
    times_series.dropna(inplace=True)
    if times_series.empty:
        return 0
    insertion_point = times_series.searchsorted(target_dt, side="right")
    return len(times_series) - insertion_point


def _get_random_query_start_timestamp_recursive(
    traces_path_resolved: str,
    min_subsequent_lines: int,
    file_prefix: str,
    recursion_depth: int,
    max_recursion_depth: int,
    all_trace_files_list: List[str],  # Must be provided by the wrapper
) -> Optional[datetime]:
    """
    Internal recursive helper to find a universally valid start timestamp.
    """
    if recursion_depth >= max_recursion_depth:
        raise RuntimeError(
            f"Max recursion depth ({max_recursion_depth}) reached. Could not find a universally valid start timestamp."
        )

    if not all_trace_files_list:  # Should be caught by wrapper, but defensive
        return None

    # Shuffle a copy for selecting a candidate source file in this attempt
    candidate_source_files_shuffled = list(all_trace_files_list)
    random.shuffle(candidate_source_files_shuffled)
    for candidate_file_path in candidate_source_files_shuffled:
        potential_timestamp: Optional[pd.Timestamp] = None
        # 1. Find a candidate timestamp within this candidate_file_path
        df = pd.read_csv(candidate_file_path, usecols=["time"])
        df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce")
        df.dropna(subset=["time"], inplace=True)
        num_lines: int = len(df)
        if num_lines >= min_subsequent_lines + 1:
            max_start_index: int = num_lines - 1 - min_subsequent_lines
            if max_start_index >= 0:
                random_valid_index: int = random.randint(0, max_start_index)
                potential_timestamp = df["time"].iloc[random_valid_index]
        is_universally_valid: bool = True
        for validation_file_path in all_trace_files_list:
            lines_after: int = count_lines_after_timestamp(potential_timestamp, validation_file_path)
            print(f"File {validation_file_path} has {lines_after} lines after the {potential_timestamp} timestamp")
            if lines_after < min_subsequent_lines:
                is_universally_valid = False
                break

        if is_universally_valid:
            return potential_timestamp  # Found a universally valid timestamp

    # If loop completes, no universally valid timestamp was found in this pass
    return _get_random_query_start_timestamp_recursive(
        traces_path_resolved,
        min_subsequent_lines,
        file_prefix,
        recursion_depth + 1,
        max_recursion_depth,
        all_trace_files_list,  # Pass the full list again
    )


def get_random_query_start_timestamp(
    traces_path: str = constants.TRACES_PATH,  # Uses default from constants or fallback
    min_subsequent_lines: int = 500,
    file_prefix: str = "WS",
    max_attempts: int = constants.DEFAULT_MAX_RECURSION_FOR_TIMESTAMP_SEARCH,  # Exposed as max_attempts
) -> Optional[datetime]:
    """
    Finds a random timestamp that is valid across ALL specified trace files.
    A timestamp is valid for a file if there are at least `min_subsequent_lines`
    data entries after this timestamp in that file.

    The process involves:
    1. Picking a random file and a random valid timestamp from it.
    2. Checking if this timestamp is also valid for all other trace files.
    3. If not, repeating the process up to `max_attempts`.

    Args:
        traces_path (str): Directory containing trace files.
        min_subsequent_lines (int): Min data lines required after the timestamp.
        file_prefix (str): Prefix for trace files (e.g., "WS").
        max_attempts (int): Max number of attempts (recursive calls) to find
                             a suitable timestamp before raising an error.

    Returns:
        Optional[datetime]: A timezone-aware datetime object (UTC) if found.
                            None if basic conditions (paths, file existence) aren't met.

    Raises:
        RuntimeError: If no suitable timestamp is found after `max_attempts`.
    """
    if not os.path.isdir(traces_path):
        # Depending on desired strictness, could raise ValueError or return None
        # print(f"Error: Traces directory '{traces_path}' not found.")
        return None

    all_trace_files: List[str] = [
        os.path.join(traces_path, f)
        for f in os.listdir(traces_path)
        if f.startswith(file_prefix) and f.endswith(".csv")
    ]

    if not all_trace_files:
        # print(f"Error: No '{file_prefix}*.csv' files found in '{traces_path}'.")
        return None

    try:
        return _get_random_query_start_timestamp_recursive(
            traces_path_resolved=traces_path,  # Pass resolved path
            min_subsequent_lines=min_subsequent_lines,
            file_prefix=file_prefix,  # Not strictly needed by recursive part if all_trace_files is passed
            recursion_depth=0,
            max_recursion_depth=max_attempts,
            all_trace_files_list=all_trace_files,
        )
    except RuntimeError:  # Catch the specific error from the recursive helper
        # print(f"Failed to find a universally valid start timestamp after {max_attempts} attempts.")
        raise  # Re-raise the error as per requirement
    except Exception as e:
        # print(f"An unexpected error occurred during timestamp search: {e}")
        # Depending on desired behavior, could return None or raise
        raise RuntimeError(f"Unexpected error during timestamp search: {e}")
