import os
import pandas as pd
import numpy as np
from itertools import combinations
from datetime import timedelta

# Helpers for nanosecond time handling
def to_epoch_ns(time_str):
    return pd.to_datetime(time_str, utc=True).value

def from_epoch_ns(epoch_ns):
    return pd.to_datetime(epoch_ns, utc=True).isoformat(timespec='nanoseconds').replace('+00:00', 'Z')

# Get all files starting with "N"
n_files = [f for f in os.listdir() if f.startswith("N") and f.endswith(".csv")]

# Generate combinations of 3 files
file_combinations = list(combinations(n_files, 3))

# Rolling window size in nanoseconds (10 minutes)
WINDOW_SIZE_NS = int(10 * 60 * 1e9)

for combo in file_combinations:
    dfs = []

    # Load files and parse time to datetime
    for file in combo:
        df = pd.read_csv(file, dtype={"time": str})
        df["timestamp"] = pd.to_datetime(df["time"], utc=True)
        df["epoch_ns"] = df["timestamp"].astype(np.int64)
        dfs.append(df)

    # Concatenate all rows from the 3 files
    combined = pd.concat(dfs, ignore_index=True)

    # Get the earliest timestamp to define the rolling windows
    min_time_ns = combined["epoch_ns"].min()
    max_time_ns = combined["epoch_ns"].max()

    # Prepare output storage
    averaged_rows = []

    # Loop through windows starting from the smallest timestamp
    window_start = min_time_ns
    while window_start < max_time_ns:
        window_end = window_start + WINDOW_SIZE_NS
        in_window = combined[(combined["epoch_ns"] >= window_start) & (combined["epoch_ns"] < window_end)]

        if not in_window.empty:
            numeric_cols = [col for col in combined.columns if col not in ["time", "timestamp", "epoch_ns"]]
            avg_values = in_window[numeric_cols].mean()
            avg_time_ns = int(in_window["epoch_ns"].mean())
            avg_values["time"] = from_epoch_ns(avg_time_ns)
            averaged_rows.append(avg_values)

        window_start = window_end

    # Convert results to DataFrame
    if averaged_rows:
        result_df = pd.DataFrame(averaged_rows)
        # Reorder columns
        final_columns = list(numeric_cols) + ["time"]
        result_df = result_df[final_columns]

        # Output filename
        base_names = [os.path.splitext(f)[0] for f in combo]
        output_filename = f"MERGED_{'_'.join(base_names)}.csv"
        result_df.to_csv(output_filename, index=False)
        print(f"Saved: {output_filename}")

# import os
# import pandas as pd
# import numpy as np
# from itertools import combinations
# from datetime import datetime, timezone

# def to_epoch_ns(time_str):
#     # Convert ISO time string to integer nanoseconds since epoch
#     return pd.to_datetime(time_str, utc=True).value

# def from_epoch_ns(epoch_ns):
#     # Convert nanoseconds since epoch to ISO 8601 with nanosecond precision and Z suffix
#     return pd.to_datetime(epoch_ns, utc=True).isoformat(timespec='nanoseconds') + 'Z'

# # Step 1: Get all files starting with "N" and ending in ".csv"
# n_files = [f for f in os.listdir() if f.startswith("N") and f.endswith(".csv")]

# # Step 2: Generate all unique combinations of three files
# file_combinations = list(combinations(n_files, 3))

# # Step 3: Process each combination
# for combo in file_combinations:
#     dfs = []

#     # Load DataFrames with 'time' as string
#     for file in combo:
#         df = pd.read_csv(file, dtype={"time": str})
#         dfs.append(df)

#     # Align all dataframes by index, trimming to shortest length
#     min_len = min(len(df) for df in dfs)
#     dfs = [df.iloc[:min_len].reset_index(drop=True) for df in dfs]

#     # === Average numeric data row-by-row ===
#     numeric_dfs = [df.drop(columns=["time"]) for df in dfs]
#     averaged_df = sum(numeric_dfs) / len(numeric_dfs)

#     # === Average 'time' column ===
#     # Convert time columns to nanosecond timestamps
#     time_arrays = [df["time"].apply(to_epoch_ns) for df in dfs]
#     time_matrix = np.vstack(time_arrays)  # shape: (3, N)
#     avg_time_ns = np.mean(time_matrix, axis=0).astype(np.int64)

#     # Convert averaged time back to ISO format
#     averaged_time = [from_epoch_ns(ns) for ns in avg_time_ns]

#     # Add to result
#     averaged_df["time"] = averaged_time

#     # Reorder columns to match original order
#     final_columns = list(numeric_dfs[0].columns) + ['time']
#     averaged_df = averaged_df[final_columns]

#     # Save merged result
#     base_names = [os.path.splitext(f)[0] for f in combo]
#     output_filename = f"MERGED_{'_'.join(base_names)}.csv"
#     averaged_df.to_csv(output_filename, index=False)
#     print(f"Merged file saved as: {output_filename}")
