import numpy as np
import os
import random
import pandas as pd

from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from Source import Producers
import constants
from mode import Mode

GLOBAL_MIN, GLOBAL_MAX = None, None


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
    current_time,
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
            "current_time",
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
            current_time,
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
            "current_time",
            "mode",
            "inferred_truth",
            "fail_counter",
            "consolidated_result",
        ]
        fields = [
            current_time,
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
    target_dt = pd.to_datetime(timestamp_str, format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce", utc=True)
    df_time_col = pd.read_csv(file_path, usecols=["time"])
    times_series = pd.to_datetime(df_time_col["time"], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce", utc=True)
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
        df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S.%fZ", errors="coerce", utc=True)
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
    file_prefix: str = constants.FILE_PREFIX,
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


def get_global_time_range(trace_files: List[str]) -> Optional[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Finds the earliest and latest timestamp across all provided trace files.
    (Implementation from previous responses)
    """
    global GLOBAL_MIN, GLOBAL_MAX

    if GLOBAL_MAX is not None and GLOBAL_MIN is not None:
        return GLOBAL_MIN, GLOBAL_MAX
    global_min_time: Optional[pd.Timestamp] = None
    global_max_time: Optional[pd.Timestamp] = None

    if not trace_files:
        return None

    for file_path in trace_files:
        df = pd.read_csv(file_path, usecols=["time"])
        df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
        df.dropna(subset=["time"], inplace=True)
        current_min_time = df["time"].min()
        current_max_time = df["time"].max()
        if global_min_time is None or current_min_time < global_min_time:
            global_min_time = current_min_time
        if global_max_time is None or current_max_time > global_max_time:
            global_max_time = current_max_time
    GLOBAL_MIN, GLOBAL_MAX = global_min_time, global_max_time
    return global_min_time, global_max_time


def define_start_attack_timestamp(
    sim_start_ts_pd: datetime,  # Now receives this as input
    traces_path: str = constants.TRACES_PATH,
    file_prefix: str = constants.FILE_PREFIX,
) -> datetime:
    """
    Determines a start timestamp for an attack, occurring after a given
    simulation_start_timestamp and after the first 1/3 of the remaining
    global data duration.
    """
    all_trace_files: List[str] = [
        os.path.join(traces_path, f)
        for f in os.listdir(traces_path)
        if f.startswith(file_prefix) and f.endswith(".csv")
    ]
    time_range_result = get_global_time_range(all_trace_files)

    _abs_data_min_time, abs_data_max_time = time_range_result
    relevant_duration = abs_data_max_time - sim_start_ts_pd
    attack_window_starts_after: pd.Timestamp = sim_start_ts_pd + (relevant_duration / 3.0)

    print(f"Debug: Sim start: {sim_start_ts_pd.isoformat()}")
    print(f"Debug: Abs data max: {abs_data_max_time.isoformat()}")
    print(f"Debug: Relevant duration: {relevant_duration}")
    print(f"Debug: Attack window must start after: {attack_window_starts_after.isoformat()}")
    start_ts = attack_window_starts_after.timestamp()
    end_ts = abs_data_max_time.timestamp()
    third_window = (end_ts - start_ts) / 3
    random_offset = random.uniform(0, third_window)
    random_timestamp = pd.to_datetime(start_ts + random_offset, unit="s", utc=True)
    print(f"Debug: Attack time: {random_timestamp.isoformat()}")

    return random_timestamp


def get_next_request_timestamp(
    current_timestamp: datetime, average_arrival_rate: float = constants.ARRIVAL_RATE_IN_SEC
) -> datetime:
    """
    Calculates the next request timestamp based on an exponential inter-arrival time.

    Args:
        current_timestamp (datetime): The timestamp of the current/last request.
        average_arrival_rate (float): The average number of requests expected
                                      per seconds.
                                      Must be greater than 0.

    Returns:
        datetime: The timestamp for the next request.

    Raises:
        ValueError: If average_arrival_rate is not positive.
    """
    if average_arrival_rate <= 0:
        raise ValueError("average_arrival_rate must be positive.")

    # The scale parameter (beta) for exponential distribution is 1/lambda (rate)
    # If arrival_rate is in queries/second, then inter_arrival_time will be in seconds.
    inter_arrival_time_seconds: float = np.random.exponential(scale=1.0 / average_arrival_rate)

    time_delta = timedelta(seconds=inter_arrival_time_seconds)

    next_timestamp: datetime = current_timestamp + time_delta

    return next_timestamp


def write_indexer_reputations(outfile, array_indexers, data_values, current_time) -> None:
    """
    Writes one line with current_time and all indexers' reputations as columns to the specified filename.

    If the file does not exist or is empty, writes a header.
    """
    file_exists = os.path.exists(outfile)
    write_header = not file_exists or os.path.getsize(outfile) == 0

    with open(outfile, "a") as f:
        if write_header:
            header = (
                ["current_time"]
                + [str(indexer.idx) for indexer in array_indexers]
                + [str(indexer.idx) + "_data" for indexer in array_indexers]
            )
            f.write(",".join(header) + "\n")
        row = (
            [str(current_time)]
            + [str(indexer.reputation) for indexer in array_indexers]
            + [str(data) for data in data_values]
        )
        f.write(",".join(row) + "\n")
