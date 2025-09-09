import os
from subprocess import Popen, PIPE

# REPUTATION_MIN
REPUTATION_MIN_arr = [-0.8, -0.6, -0.4, -0.2]
REPUTATION_MIN_arr = [-0.4]

# RATIO_MALICIOUS
RATIO_MALICIOUS_arr = [0.1, 0.2, 0.3, 0.4, 0.5]
RATIO_MALICIOUS_arr = [0.1, 0.3, 0.4, 0.5]

# RATIO_MALICIOUS ORACLES
RATIO_MALICIOUS_ORACLES_arr = [0.1, 0.05, 0.0]
RATIO_MALICIOUS_ORACLES_arr = [0.0]

# ALPHA
ALPHA_arr = [0.5]

# BETA
BETA_arr = [0.9]

# TOLERANCE
TOLERANCE_arr = [3.0]

# ALGORITHM
ALGO = [0, 1, 2]
ALGO = [2]

# TRUTH INFERENCE
TRUTH = [0, 1, 2, 3]
TRUTH = [1]

# NUMBER OF BLOCKCHAINS
N_BLOCKCHAINS = [3]
FAV_CHAIN_arr = [-1, 0, 1, 2, 3]  # 0 means no favourite chain, otherwise it is the index of the chain in the list of chains

# COST AND TIME PARAMETER
COST_TIME_PARAM_arr = [0, 0.25, 0.5, 0.75, 1.0]
COST_TIME_PARAM_arr = [0.5]

ARRIVAL_RATE_arr = ['uniform']

# FILE
FILE_OUT_path = "results-distributed"
FILE_OUT_prefix = "REP"

REPETITIONS = 20
REP_START = 0

OVERWRITE = True

if not os.path.exists(FILE_OUT_path):
    os.makedirs(FILE_OUT_path)

counter = 0
total = REPETITIONS * len(TRUTH) * len(REPUTATION_MIN_arr) * len(COST_TIME_PARAM_arr) * len(RATIO_MALICIOUS_arr)* len(ALGO)*len(ARRIVAL_RATE_arr)*len(FAV_CHAIN_arr)*len(RATIO_MALICIOUS_ORACLES_arr)

for rep in range(REP_START, REP_START + REPETITIONS):
    for mal_orac in RATIO_MALICIOUS_ORACLES_arr:
        for reputation_min in REPUTATION_MIN_arr:
            for ratio_malicious in RATIO_MALICIOUS_arr:
                for cost_time_param in COST_TIME_PARAM_arr:
                    for blockchain_num in N_BLOCKCHAINS:
                        for algo in ALGO:
                            for arrival_rate in ARRIVAL_RATE_arr:
                                for truth in TRUTH:
                                    for fav_chain in FAV_CHAIN_arr:   

                                        filepath = os.path.join(FILE_OUT_path, 
                                            "_".join([
                                                FILE_OUT_prefix,
                                                str(reputation_min),
                                                str(ratio_malicious),
                                                str(cost_time_param),
                                                str(fav_chain),
                                                str(rep),
                                                str(algo),
                                                str(arrival_rate),
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
                                                "--reputation_min", str(reputation_min),
                                                "--ratio_malicious_indexers", str(ratio_malicious),
                                                "--ratio_malicious_oracles", str(mal_orac),
                                                "--file_out", str(filepath),
                                                "--algo", str(algo),
                                                "--truth", str(truth),
                                                "--arrival_rate", str(arrival_rate),
                                                "--cost-time-param", str(cost_time_param),
                                                "--fav_chain", str(fav_chain),
                                            ])
                                            stdout, stderr = process.communicate()
            
            
