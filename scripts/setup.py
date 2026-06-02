"""
Run this script to initially copy the ground truth files into the Submissions/ folder, so that they appear in the leaderboard.
"""

import shutil
import os

from pathlib import Path

# Where this script lives (in the /scripts directory)
root = Path(__file__)

ground_truths_path = root.parents[1] / "public" / "Ground_Truths"
if not ground_truths_path.exists():
    raise NotADirectoryError(ground_truths_path)

submissions_path = root.parents[1] / "Submissions"
if not submissions_path.exists():
    raise NotADirectoryError(submissions_path)

# Find all challenges (subfolder names of the ground truth folder)
challenges = [d.name for d in ground_truths_path.iterdir() if d.is_dir()]

print(f"{challenges=}")

for challenge in challenges:
    gt_challenge_folder = ground_truths_path / challenge
    dst_folder = submissions_path / challenge
    if not dst_folder.exists():
        os.mkdir(dst_folder)
        print(f"Created: {dst_folder}")
    
    for gt_file in gt_challenge_folder.glob("*.tif"):
        gt_submission_file = dst_folder / "ground_truth.tif"  # Call it ground_truth.tif
        shutil.copy(src=gt_file, dst=gt_submission_file)
        print(f"Copied {gt_file} into {dst_folder}")
        break

print("Setup complete!")