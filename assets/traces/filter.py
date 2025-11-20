import os
import pandas as pd

# Cutoff timestamp as datetime
cutoff_time = pd.to_datetime("2025-06-04T11:56:31.452460962Z")

# Loop through all CSV files in the current directory
for filename in os.listdir():
    if filename.endswith(".csv") and not filename.startswith("N"):
        # Read the CSV while keeping the original 'time' column as string
        df = pd.read_csv(filename, dtype={"time": str})

        # Parse time to datetime only for filtering
        time_parsed = pd.to_datetime(df["time"], utc=True)

        # Filter rows where parsed time is after the cutoff
        filtered_df = df[time_parsed > cutoff_time]

        # Write the filtered data to new CSV with the 'N' prefix
        new_filename = "N" + filename
        filtered_df.to_csv(new_filename, index=False)

        print(f"Filtered file saved as: {new_filename}")
