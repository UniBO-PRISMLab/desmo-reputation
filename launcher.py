import os
from subprocess import Popen, PIPE

# REPUTATION_MIN
REPUTATION_MIN_arr = [-0.8, -0.6, -0.4, -0.2]
# REPUTATION_MIN_arr = [-0.6, -0.4]

# RATIO_MALICIOUS
RATIO_MALICIOUS_arr = [0.25, 0.5, 0.75, 1.0]
RATIO_MALICIOUS_arr = [0.1, 0.2, 0.3, 0.4, 0.5]

# RATIO_MALICIOUS ORACLES
RATIO_MALICIOUS_ORACLES_arr = [0.2, 0.1, 0.0]

# ALPHA
ALPHA_arr = [0.1, 0.3, 0.5, 0.7, 0.9]
ALPHA_arr = [0.5]

# BETA
BETA_arr = [0.0, 0.25, 0.5, 0.75, 1.0]
BETA_arr = [0.9]

# TOLERANCE
TOLERANCE_arr = [3.0]

# ALGORITHM
ALGO = [0, 1, 2]

# TRUTH INFERENCE
TRUTH = [0, 1, 2]

ARRIVAL_RATE_arr = ['uniform', 'bursty']

# FILE
FILE_OUT_path = "results-truth-inf"
FILE_OUT_prefix = "REP"

#REPETITIONS = 20
REPETITIONS = 10
REP_START = 5

OVERWRITE = False

if not os.path.exists(FILE_OUT_path):
    os.makedirs(FILE_OUT_path)

# 1920 outfiles old

counter = 0
total = REPETITIONS * len(TRUTH) * len(REPUTATION_MIN_arr) * len(RATIO_MALICIOUS_arr)* len(ALPHA_arr)* len(TOLERANCE_arr)* len(ALGO)*len(ARRIVAL_RATE_arr)*len(BETA_arr)*len(RATIO_MALICIOUS_ORACLES_arr)

for mal_orac in RATIO_MALICIOUS_ORACLES_arr:
    for rep in range(REP_START, REPETITIONS):
        for reputation_min in REPUTATION_MIN_arr:
            for ratio_malicious in RATIO_MALICIOUS_arr:
                for alpha in ALPHA_arr:
                    for tolerance in TOLERANCE_arr:
                        for algo in ALGO:
                            for arrival_rate in ARRIVAL_RATE_arr:
                                for beta in BETA_arr:
                                    for truth in TRUTH:

                                        filepath = os.path.join(FILE_OUT_path, 
                                            "_".join([
                                                FILE_OUT_prefix,
                                                str(reputation_min),
                                                str(ratio_malicious),
                                                str(alpha),
                                                str(tolerance),
                                                str(rep),
                                                str(algo),
                                                str(arrival_rate),
                                                str(beta),
                                                str(mal_orac),
                                                str(truth)
                                            ]) + ".csv"
                                        )
                                        counter += 1
                                        print(f"\n\n\t{counter}/{total}******Going for " + filepath + "******")

                                        # if os.path.exists(filepath):
                                        #     with open(filepath, 'r') as tempfile:
                                        #         count = 0
                                        #         for count, line in enumerate(tempfile):
                                        #             pass
                                        #     if not (count + 1) == 10000:
                                        #         os.remove(filepath)
                                        #         print("Replacing " + filepath)
                                

                                        if OVERWRITE or not os.path.exists(filepath):

                                            process = Popen([
                                                'python3', 
                                                'reputation.py',
                                                str(reputation_min),
                                                str(ratio_malicious),
                                                str(alpha),
                                                str(tolerance),
                                                str(filepath),
                                                str(algo),
                                                str(arrival_rate),
                                                str(beta),
                                                str(mal_orac),
                                                str(truth)
                                            ])
                                            stdout, stderr = process.communicate()
                
                
