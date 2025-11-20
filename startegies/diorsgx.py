from datetime import datetime
from statistics import mean
import sys

from Source import Producers
import constants
from truth_inference_checker import TruthInferenceFunction
import utils

fail_counter = 0
sequential_fail_counter = 0


def do_DiorSGX(timestamp: datetime, file, truth_checker: TruthInferenceFunction) -> None:
    """
    Executes one simulation step using the DiorSGX strategy.

    Args:
        epoch (int): Current epoch number.
        file: Output file object.
        truth_checker (TruthInferenceFunction): Function used to validate inferred truth.
    """
    global fail_counter, sequential_fail_counter

    values = [source.generate_sample(timestamp) for source in Producers.values()]
    inferred_truth = mean([item for row in values for item in row])

    if inferred_truth >= constants.THRESHOLD:
        sequential_fail_counter += 1
    else:
        sequential_fail_counter = 0


    fail_counter += sequential_fail_counter

    utils.write_simulation_result(
        outfile=file,
        current_time=timestamp,
        mode_name=constants.MODE,
        inferred_truth=inferred_truth,
        fail_counter=fail_counter,
        consolidated_result=sequential_fail_counter >= constants.CONTRACT_READS,
    )
