import os
from subprocess import Popen, PIPE

# REPUTATION_MIN
REPUTATION_MIN_arr = [-0.8, -0.6, -0.4, -0.2]
#REPUTATION_MIN_arr = [-0.6, -0.4]

# RATIO_MALICIOUS
RATIO_MALICIOUS_arr = [0.25, 0.5, 0.75, 1.0]
#RATIO_MALICIOUS_arr = [0.25, 0.75]

# ALPHA
ALPHA_arr = [0.1, 0.3, 0.5, 0.7]
#ALPHA_arr = [0.5]

# TOLERANCE
TOLERANCE_arr = [3.0, 1.0, 5.0]
#TOLERANCE_arr = [3.0]

# ALGORITHM
ALGO = [0, 1, 2]

# FILE
FILE_OUT_path = "results"
FILE_OUT_prefix = "REP"

REPETITIONS = 10
#REPETITIONS = 1

OVERWRITE = False

if not os.path.exists(FILE_OUT_path):
    os.makedirs(FILE_OUT_path)

# 1920 outfiles

for rep in range(REPETITIONS):
    for reputation_min in REPUTATION_MIN_arr:
        for ratio_malicious in RATIO_MALICIOUS_arr:
            for alpha in ALPHA_arr:
                for tolerance in TOLERANCE_arr:
                    for algo in ALGO:

                        filepath = os.path.join(FILE_OUT_path, 
                            "_".join([
                                FILE_OUT_prefix,
                                str(reputation_min),
                                str(ratio_malicious),
                                str(alpha),
                                str(tolerance),
                                str(rep),
                                str(algo)
                            ]) + ".csv"
                        )

                        print("Going for " + filepath)

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
                                str(algo)
                            ])
                            stdout, stderr = process.communicate()
                
                
