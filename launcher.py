import os
import subprocess
import sys

# === CONFIG ===
mode = "ZONIA"
FARMERS_RATIO_arr = [0.7]#[x / 10 for x in range(3, 7, 1)]
if mode == "ZONIA":
    OTHER_RATIO_arr = [0.3]#[0.0, 0.1, 0.2, 0.3]  # As portion of the total producers
else:
    OTHER_RATIO_arr = [0.0]

START_REPETITION = 0
REPETITIONS =100
OVERWRITE = False

FILE_OUT_PATH = "results-owner-ratios"
FILE_OUT_PREFIX = f"OWNER_RATIOS_{mode}"

DEFAULTS = {
    "contract_reads": 5,
    "threshold": 30,
    "attack_duration": 30,
}

# === SETUP ===

if not os.path.exists(FILE_OUT_PATH):
    os.makedirs(FILE_OUT_PATH)

total = (REPETITIONS * len(FARMERS_RATIO_arr) * len(OTHER_RATIO_arr)) - START_REPETITION
counter = 0

# === MAIN LOOP ===

for other_ratio in OTHER_RATIO_arr:
    for farmer_ratio in FARMERS_RATIO_arr:
        insurance_ratio = 1.0 - farmer_ratio

        # Format float values to two decimal places
        f_ratio_str = f"{farmer_ratio:.2f}"
        i_ratio_str = f"{insurance_ratio:.2f}"
        o_ratio_str = f"{other_ratio:.2f}"

        for rep in range(START_REPETITION, REPETITIONS):
            filename = (
                "_".join([FILE_OUT_PREFIX, f"f{f_ratio_str}", f"i{i_ratio_str}", f"o{o_ratio_str}", f"r{rep}"])
                + ".csv"
            )

            filepath = os.path.join(FILE_OUT_PATH, filename)

            counter += 1
            print(f"\n\n\t{counter}/{total} ****** Running: {filepath} ******")

            if OVERWRITE or not os.path.exists(filepath):
                cmd = [
                    "python3",
                    "reputation.py",
                    "--file_out",
                    filepath,
                    "--contract_reads",
                    str(DEFAULTS["contract_reads"]),
                    "--attack_duration",
                    str(DEFAULTS["attack_duration"]),
                    "--farmers_ratio",
                    f_ratio_str,
                    "--insurance_ratio",
                    i_ratio_str,
                    "--other_ratio",
                    o_ratio_str,
                ]

                subprocess.run(cmd)
                #sys.exit()
