import pandas as pd
from datetime import datetime, timedelta  # tzinfo, timezone
import os
import random
from typing import Dict, Set, Optional, Any, List

import numpy as np

# Assuming constants.py and utils.py are accessible
import constants
import utils

# Global variable to assign an ID to Sources
source_incremental_idx: int = 1

# --- Trace File Management ---
_available_trace_files: Optional[List[str]] = None
_available_trace_files_virtual: Optional[List[str]] = None
_assigned_trace_files: Set[str] = set()


def _initialize_available_traces() -> None:
    """
    Scans the TRACES_PATH for CSV files starting with 'NWS' and populates
    the _available_trace_files list. This function is called lazily.
    Files are shuffled to ensure randomness when picking.
    """
    global _available_trace_files, _available_trace_files_virtual
    if _available_trace_files is not None:  # Ensure it runs only once
        return

    _available_trace_files = []
    _available_trace_files_virtual = []
    # Use TRACES_PATH from constants, with a fallback default
    if not os.path.exists(constants.TRACES_PATH) or not os.path.isdir(constants.TRACES_PATH):
        print(f"Warning: Traces directory '{constants.TRACES_PATH}' not found or is not a directory.")
        return  # _available_trace_files remains an empty list

    for filename in os.listdir(constants.TRACES_PATH):
        if filename.startswith(constants.FILE_PREFIX) and filename.endswith(".csv"):
            _available_trace_files.append(os.path.join(constants.TRACES_PATH, filename))
        if filename.startswith("MERGED"):
            #print(os.path.join(constants.TRACES_PATH, filename))
            _available_trace_files_virtual.append(os.path.join(constants.TRACES_PATH, filename))
    random.shuffle(_available_trace_files)  # Shuffle for random assignment


def _get_random_trace_file() -> str:
    """
    Selects a random, unassigned trace file path.
    Marks the file as assigned and removes it from the list of available files.

    Returns:
        str: The path to an unassigned trace file.

    Raises:
        RuntimeError: If no unassigned trace files are available.
    """
    global _available_trace_files, _available_trace_files_virtual, _assigned_trace_files

    if _available_trace_files is None:
        _initialize_available_traces()

    if (
        not _available_trace_files and not _available_trace_files_virtual
    ):  # True if None or empty list after initialization attempt
        raise RuntimeError("No more trace files available for new Source instances.")

    if len(_available_trace_files) > 0:
        file_path: str = _available_trace_files.pop()
    else:
        file_path: str = _available_trace_files_virtual.pop()

    _assigned_trace_files.add(file_path)
    return file_path


# --- Source Class ---


class Source:
    """
    SOURCE:

    Represents a data source that reads its values from a specific trace file.
    Each Source instance is associated with a unique trace file from the
    directory specified by `constants.TRACES_PATH`.

    Data is queried by specifying a data type (column name) and a timestamp.
    The source returns the value from the last data point at or before the
    given timestamp.

    Original concepts of synthetic data generation (variance, ground truth, etc.)
    are replaced by reading from trace files. Scoring mechanisms may need adaptation.
    """

    def __init__(self, trusted: bool = True) -> None:
        """
        Initializes a Source instance.

        Args:
            trusted (bool): Indicates if the source is considered trusted.
                            Its direct impact on data generation is altered
                            due to reading from traces, but it can be used for
                            other logic (e.g., scoring bias).

        Raises:
            RuntimeError: If no trace file can be assigned (e.g., all are used).
            Exception: If there's an error loading or processing the trace file.
        """
        global source_incremental_idx
        self.idx: int = source_incremental_idx
        source_incremental_idx += 1

        self._trusted: bool = trusted

        # Defectiveness: Original logic was for synthetic data.
        # Set self.defective based on constants if you want to simulate defects on top of traces.
        # Example:
        # self.defective: bool = (getattr(constants, 'SOURCE_DEFECTIVE', False) and
        #                         np.random.rand() < getattr(constants, 'SOURCE_RATIO_DEFECTIVE', 0.1))
        self.defective: bool = False  # Defaulting to non-defective for trace reading
        try:
            self.trace_file_path: str = _get_random_trace_file()
            self.is_virtual =  self.trace_file_path.startswith("MERGED")                
            self.data: pd.DataFrame = self._load_trace_data()
            
        except RuntimeError:  # Specifically "No more trace files"
            source_incremental_idx -= 1  # Roll back ID increment
            raise
        except Exception as e:  # Other errors (file loading, parsing)
            source_incremental_idx -= 1  # Roll back ID increment
            raise Exception(f"Failed to initialize Source {self.idx} (ID tentative). Error: {e}")

        # Attributes related to synthetic data generation are now placeholders or re-evaluated.
        self.variance: float = 0.0  # Was: random variance for synthetic data.
        self.avg_speed: float = constants.SOURCE_BASE_SPEED

        self.last_generated_sample: Optional[Any] = None
        self.last_request_at: Optional[Dict[str, Any]] = None

        # Scoring attributes - their calculation will change as last_generated_sample is a single value.
        self.last_score_array: Optional[np.ndarray] = None
        self.last_deviation_array: Optional[np.ndarray] = None
        self.last_consistency_array: Optional[np.ndarray] = None
        self.last_score: Optional[float] = None
        self.internal_reputation: float = constants.SOURCE_SOURCE_REPUTATION_INIT
        self.attacker_variance = constants.ATTACKER_VARIANCE

    def _load_trace_data(self) -> pd.DataFrame:
        """
        Loads and preprocesses data from the Source's assigned trace file.
        The 'time' column is converted to datetime objects and the DataFrame is sorted by time.
        The first column in CSV is assumed to be an unnamed index.
        """
        try:
            # Assumes CSV header: ,col1,col2,... (unnamed first column for index)
            df = pd.read_csv(self.trace_file_path, index_col=0)
        except FileNotFoundError:
            raise FileNotFoundError(f"Trace file not found: {self.trace_file_path}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Trace file is empty: {self.trace_file_path}")
        except Exception as e:  # Catch other pandas read_csv errors
            raise Exception(f"Error reading CSV file {self.trace_file_path}: {e}")

        if "time" not in df.columns:
            raise ValueError(f"'time' column not found in {self.trace_file_path}.")

        try:
            # Time format example: 2025-03-27T14:38:47.170851094Z
            # '%Y-%m-%dT%H:%M:%S.%f%z' handles Zulu (UTC) suffix and fractional seconds.
            print(df["time"])
            df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S.%f%z", errors="coerce")
        except Exception as e:
            raise ValueError(
                f"Error parsing 'time' column in {self.trace_file_path}. "
                f"Ensure format is like 'YYYY-MM-DDTHH:MM:SS.fffffffffZ'. Error: {e}"
            )
        df.dropna(subset=["time"], inplace=True)  # Remove rows where time conversion failed
        if df.empty:
            raise ValueError(f"No valid time entries found in {self.trace_file_path} after parsing.")

        df.sort_values(by="time", inplace=True)
        return df

    @property
    def trusted(self) -> bool:
        return self._trusted

    @trusted.setter
    def trusted(self, value: bool) -> None:
        self._trusted = value
        # Original: self.set_variance(). set_variance is removed as it's for synthetic data.
        # If 'trusted' status should influence other parameters for trace-based sources,
        # that logic would go here.

    def generate_sample(
        self,
        current_time: datetime,
        data_type: str = "temperature",
        n_samples: int = 1,
        variance: float = 0.01,
        max_data_staleness_in_sec: int = constants.MAX_DATA_STALENESS_IN_SEC,  # New parameter
    ) -> Optional[List[float]]:
        self.last_request_at = current_time
        if self.trusted:
            if self.data is None or self.trace_file_path is None:
                print(f"Warning: Source {self.idx} is trusted but has no trace data loaded.")
                self.last_generated_sample = None
                return None

            if not isinstance(data_type, str) or data_type not in self.data.columns:
                self.last_generated_sample = None
                return None

            idx_after = self.data["time"].searchsorted(current_time, side="right")
            if idx_after == 0:
                self.last_generated_sample = None
                return None

            value = self.data.iloc[idx_after - 1][data_type]
            value_timestamp = self.data.iloc[idx_after - 1]["time"]
            # print(f"time delay:{current_time.timestamp() - value_timestamp.timestamp()}")
            if current_time.timestamp() - value_timestamp.timestamp() >= (max_data_staleness_in_sec):
                self.last_generated_sample = [None for i in range(n_samples)]
                return self.last_generated_sample

            base = float(value)
            variation_range = variance * base
            samples = np.random.uniform(base - variation_range, base + variation_range, size=n_samples).tolist()
            self.last_generated_sample = samples
        else:
            samples = np.random.normal(loc=constants.FALSE_TRUTH, scale=self.attacker_variance, size=n_samples)
            self.last_generated_sample = samples

        return self.last_generated_sample

    def generate_delay(self) -> float:
        """Generates a simulated processing or network delay."""
        return np.random.normal(self.avg_speed, constants.SOURCE_SPEED_VARIANCE)

    def update_score(self, _inferred_truth):
        # How much values are distant from the GROUND TRUTH
        self.last_score_array = np.array(
            [
                utils.constraintFunction(abs(x - _inferred_truth), constants.TOLERANCE)
                if x is not None
                else utils.constraintFunction(x or 0, constants.TOLERANCE)
                for x in self.last_generated_sample
            ]
        )
        valid_samples = [x for x in self.last_generated_sample if x is not None]
        mean = np.mean(valid_samples)
        # How much values are distant from the LOCAL MEAN
        self.last_deviation_array = np.array(
            [
                utils.constraintFunction(abs(x - mean), constants.TOLERANCE)
                if x is not None
                else utils.constraintFunction(0.0, constants.TOLERANCE)
                for x in self.last_generated_sample
            ]
        )
        std = np.std([x - mean for x in valid_samples]) if valid_samples else 1e-6  # avoid division by 0
        self.last_consistency_array = np.array(
            [
                utils.constraintFunction(abs(x - mean), std) if x is not None else utils.constraintFunction(0.0, std)
                for x in self.last_generated_sample
            ]
        )

        # Calculate the rating using the new equation balanced by a parameter BETA.
        # INFO: Originally returning the minium (a.k.a. the best)
        # ----> self.last_score = np.min(self.last_score_array)
        self.last_score = (constants.SOURCE_BETA_SOURCE * np.mean(self.last_score_array)) + (
            (1.0 - constants.SOURCE_BETA_SOURCE) * np.mean(self.last_deviation_array)
        )

        # Update the internal reputation, this may help the INdexer in selecting sources...
        self.internal_reputation = self.last_score * constants.SOURCE_ALPHA_SOURCE + self.internal_reputation * (
            1 - constants.SOURCE_ALPHA_SOURCE
        )

    def print_self(self, verbose: bool = False) -> None:
        """Prints information about the Source instance."""
        head: str = "Trusted" if self.trusted else "Untrusted"
        trace_file_basename: str = (
            os.path.basename(self.trace_file_path)
            if hasattr(self, "trace_file_path") and self.trace_file_path
            else "N/A"
        )
        base_info: str = f"PRODUCER: {self.idx} - {head} - Trace File: {trace_file_basename}"

        if not verbose:
            print(base_info)
        else:
            score_array_str = "N/A"
            if self.last_score_array is not None and len(self.last_score_array) > 0:
                # Assuming score_array contains one element for the single sample
                score_array_str = f"{self.last_score_array[0]:.4f}"

            print(
                f"{base_info}"
                f"\n\t Last Request: {self.last_request_at}"
                f"\n\t Last Sample Value: {self.last_generated_sample}"
                f"\n\t Last Score (vs inferred truth, component): {score_array_str}"
                f"\n\t Last Overall Rating: {self.last_score:.4f if self.last_score is not None else 'N/A'}"
                f"\n\t Internal Reputation: {self.internal_reputation:.4f}"
            )


# --- Global Producers Dictionary and Factory ---
Producers: Dict[int, Source] = {}


def generate_new_producer(trusted: bool = True) -> int:
    """
    Factory method to create a new Source, associate it with a trace file,
    and add it to the global Producers dictionary.

    Args:
        trusted (bool): Initial trusted status for the new source.

    Returns:
        int: The ID of the newly created Source.

    Raises:
        RuntimeError: If a Source cannot be created (e.g., no more trace files).
        Exception: Other exceptions during Source initialization (e.g., file loading issues).
    """
    # _initialize_available_traces() is called lazily by _get_random_trace_file if needed.

    source_instance = Source(trusted=trusted)
    Producers[source_instance.idx] = source_instance
    return source_instance.idx
