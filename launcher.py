import os
import subprocess
import sys

# === CONFIG ===
mode = "DIOR"

START_REPETITION = 0
REPETITIONS = 30
NUMBER_OF_SOURCES = [8]
OVERWRITE = True
ATTACKERS = [6]
FILE_OUT_PATH = "assets/results"
FILE_OUT_PREFIX = f"METROAGRIFOR_{mode}"

# === SETUP ===

if not os.path.exists(FILE_OUT_PATH):
    os.makedirs(FILE_OUT_PATH)

total = (REPETITIONS) - START_REPETITION
counter = 0

# === MAIN LOOP ===
for sources in NUMBER_OF_SOURCES:
    for attacker_configuration in ATTACKERS:
        for rep in range(START_REPETITION, REPETITIONS):
            filename = "_".join([FILE_OUT_PREFIX,f"s{sources}" ,f"a{attacker_configuration}", f"r{rep}"]) + ".csv"

            filepath = os.path.join(FILE_OUT_PATH, filename)

            counter += 1
            print(f"\n\n\t{counter}/{total} ****** Running: {filepath} ******")

            if OVERWRITE or not os.path.exists(filepath):
                cmd = [
                    "python3",
                    "reputation.py",
                    "--file_out",
                    filepath,
                    "--number_malicious_sources",
                    str(attacker_configuration,),
                    "--number_of_sources",
                    str(sources)
                ]
                subprocess.run(cmd)
                # sys.exit()
