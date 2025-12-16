
import numpy as np


def _object_count(mask: np.ndarray) -> int:
    uniques = np.unique(mask)
    n_objects = len(uniques)
    if 0 in uniques:  # 0 = background by convention; not counted
        n_objects -= 1
    return n_objects


def object_count_score(gtruth_mask: np.ndarray, submission_mask: np.ndarray) -> float:
    """
    Returns a score in the range [0-1] based on the relative error on object count.
    """
    n_gt = _object_count(gtruth_mask)
    n_sub = _object_count(submission_mask)
    count_score = np.abs(n_gt - n_sub) / n_gt
    return 1 - count_score


def binary_iou_score(gtruth_mask: np.ndarray, submission_mask: np.ndarray) -> float:
    """
    Intersection over union between the binary ground truth and submitted mask.
    """
    binary_gt = gtruth_mask > 0
    binary_sub = submission_mask > 0
    intersection = np.logical_and(binary_gt, binary_sub).sum()
    union = np.logical_or(binary_gt, binary_sub).sum()
    return intersection / union