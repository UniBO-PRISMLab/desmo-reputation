from typing import Callable, Dict

import constants

TruthInferenceFunction = Callable[[float, float], bool]

truth_inference_checkers: Dict[str, TruthInferenceFunction] = {
    "greater_than": lambda value, threshold=constants.THRESHOLD: value > threshold,
    "greater_equal": lambda value, threshold=constants.THRESHOLD: value >= threshold,
    "less_than": lambda value, threshold=constants.THRESHOLD: value < threshold,
    "less_equal": lambda value, threshold=constants.THRESHOLD: value <= threshold,
    "equal": lambda value, threshold=constants.THRESHOLD: value == threshold,
    "within_range": lambda value, threshold=constants.GROUND_TRUTH: abs(value - threshold) <= constants.TOLERANCE,
}
