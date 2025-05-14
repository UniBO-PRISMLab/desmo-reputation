from statistics import mean

from Source import Producers
import constants
from truth_inference_checker import TruthInferenceFunction
import utils

fail_counter = 0
sequential_fail_counter = 0 

def do_DiorSGX(epoch: int, file, truth_checker: TruthInferenceFunction) -> None:
    """
    Executes one simulation step using the DiorSGX strategy.

    Args:
        epoch (int): Current epoch number.
        file: Output file object.
        truth_checker (TruthInferenceFunction): Function used to validate inferred truth.
    """
    global fail_counter, sequential_fail_counter

    values = [source.generateSample() for source in Producers.values()]
    inferred_truth = mean([item for row in values for item in row])
    is_valid = truth_checker(inferred_truth)

    if not is_valid:
        sequential_fail_counter += 1
    else:
        sequential_fail_counter = 0

    fail_counter += sequential_fail_counter


    utils.write_simulation_result(
        outfile=file,
        epoch=epoch,
        mode_name=constants.MODE,
        inferred_truth=inferred_truth,
        fail_counter=fail_counter,
        consolidated_result= sequential_fail_counter >= constants.CONTRACT_READS
    )