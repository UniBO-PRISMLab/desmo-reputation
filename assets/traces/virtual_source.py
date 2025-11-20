import pandas as pd
from datetime import datetime
import os
import random
from typing import Dict, Set, Optional, Any, List

import numpy as np

# Assuming constants.py and utils.py are accessible
import Source
import constants

# Global variable to assign an ID to Sources
source_incremental_idx: int = 1

# --- Trace File Management ---
_available_trace_files: Optional[List[str]] = None
_assigned_trace_files: Set[str] = set()


def _initialize_available_traces() -> None:
    """
    Scans the TRACES_PATH for CSV files starting with 'NWS' and populates
    the _available_trace_files list. This function is called lazily.
    Files are shuffled to ensure randomness when picking.
    """
    global _available_trace_files
    if _available_trace_files is not None:  # Ensure it runs only once
        return

    _available_trace_files = []
    # Use TRACES_PATH from constants, with a fallback default
    if not os.path.exists(constants.TRACES_PATH) or not os.path.isdir(constants.TRACES_PATH):
        print(f"Warning: Traces directory '{constants.TRACES_PATH}' not found or is not a directory.")
        return  # _available_trace_files remains an empty list

    for filename in os.listdir(constants.TRACES_PATH):
        if filename.startswith(constants.FILE_PREFIX) and filename.endswith(".csv"):
            _available_trace_files.append(os.path.join(constants.TRACES_PATH, filename))

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
    global _available_trace_files, _assigned_trace_files

    if _available_trace_files is None:
        _initialize_available_traces()

    if not _available_trace_files:  # True if None or empty list after initialization attempt
        raise RuntimeError("No more trace files available for new Source instances.")

    file_path: str = _available_trace_files.pop()
    _assigned_trace_files.add(file_path)
    return file_path


class VirtualSource(Source):
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

    def __init__(self, min_files: int, max_files: int, trusted: bool = True) -> None:
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

        files_to_base = random.randint(min_files, max_files)
        try:
            self.trace_file_path: List[str] = [_get_random_trace_file() for _ in range(files_to_base)]
            self.data: List[pd.DataFrame] = {
                self._load_trace_data(trace_file_path) for trace_file_path in self.trace_file_path
            }
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

    def _load_trace_data(self, trace_file_path: str) -> pd.DataFrame:
        """
        Loads and preprocesses data from the Source's assigned trace file.
        The 'time' column is converted to datetime objects and the DataFrame is sorted by time.
        The first column in CSV is assumed to be an unnamed index.
        """
        try:
            df = pd.read_csv(trace_file_path, index_col=0)
        except FileNotFoundError:
            raise FileNotFoundError(f"Trace file not found: {trace_file_path}")
        except pd.errors.EmptyDataError:
            raise ValueError(f"Trace file is empty: {trace_file_path}")
        except Exception as e:  # Catch other pandas read_csv errors
            raise Exception(f"Error reading CSV file {trace_file_path}: {e}")

        if "time" not in df.columns:
            raise ValueError(f"'time' column not found in {trace_file_path}.")

        try:
            # Time format example: 2025-03-27T14:38:47.170851094Z
            # '%Y-%m-%dT%H:%M:%S.%f%z' handles Zulu (UTC) suffix and fractional seconds.
            print(df["time"])
            df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S.%f%z", errors="coerce")
        except Exception as e:
            raise ValueError(
                f"Error parsing 'time' column in {trace_file_path}. "
                f"Ensure format is like 'YYYY-MM-DDTHH:MM:SS.fffffffffZ'. Error: {e}"
            )
        df.dropna(subset=["time"], inplace=True)  # Remove rows where time conversion failed
        if df.empty:
            raise ValueError(f"No valid time entries found in {trace_file_path} after parsing.")

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

        
            idx_after = [data["time"].searchsorted(current_time, side="right") for data in self.data]
            value = np.mean([self.data[i].iloc[idx_after[i] - 1][data_type] for i in range(len(self.data))])
            value_timestamp = self.data[0].iloc[idx_after[0] - 1]["time"]
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
