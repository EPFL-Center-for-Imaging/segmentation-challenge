"""
This script is to be run by workshop organizers.

It periodically computes the leaderboards and saves the results as CSVs in the Leaderboard/ folder.
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import skimage.io

from metrics import object_count_score, binary_iou_score

# Refresh rate of the script
UPDATE_INTERVAL_SEC = 5

# Where this script lives (in the /Scripts directory)
root = Path(__file__)

ground_truths_path = root.parents[1] / "public" / "Ground_Truths"
if not ground_truths_path.exists():
    raise NotADirectoryError(ground_truths_path)

submissions_path = root.parents[1] / "Submissions"
if not submissions_path.exists():
    raise NotADirectoryError(submissions_path)

leaderboard_path = root.parents[1] / "Leaderboard"
if not leaderboard_path.exists():
    raise NotADirectoryError(leaderboard_path)

# Find all challenges (subfolder names of the ground truth folder)
challenges = [d.name for d in ground_truths_path.iterdir() if d.is_dir()]

# Read all ground truth masks
ground_truths = {}
for challenge in challenges:
    gt_challenge_folder = ground_truths_path / challenge
    for gt_file in gt_challenge_folder.glob("*.tif"):
        gt_mask = skimage.io.imread(gt_file)
        break  # There should only be one ground truth
    ground_truths[challenge] = gt_mask

# Start the refresh loop
while True:
    # Find all participants (based on the file names of their submissions)
    participants = []
    for challenge in challenges:
        submission_challenge_folder = submissions_path / challenge
        for gt_file in submission_challenge_folder.glob("*.tif"):
            participant = gt_file.stem
            if participant not in participants:
                participants.append(participant)
    n_participants = len(participants)

    # Evaluate participant scores
    records = []
    for challenge in challenges:
        gt_mask = ground_truths[challenge]
        submission_challenge_folder = submissions_path / challenge

        for gt_file in submission_challenge_folder.glob("*.tif"):
            mask = skimage.io.imread(gt_file)
            
            oc_score = object_count_score(gt_mask, mask)

            # Let's avoid that people submit cropped images and crash the script
            if gt_mask.shape == mask.shape:
                iou_score = binary_iou_score(gt_mask, mask)
            else:
                iou_score = 0
            
            overall_score = np.mean([oc_score, iou_score])  # Simple average between object count and IoU metrics

            participant = gt_file.stem
            
            records.append(
                {
                    "participant": participant,
                    "challenge": challenge,
                    "oc_score": oc_score,
                    "iou_score": iou_score,
                    "overall_score": overall_score,
                }
            )

    # DataFrame representation of the leaderboard
    df = pd.DataFrame.from_records(records)

    # Add points for each challenge (points = rank in descending order, for example 1st of 22 participants gets 22 points).
    for challenge in challenges:
        df_challenge = df[df['challenge'] == challenge].sort_values(by="overall_score", ascending=False).drop("challenge", axis="columns")
        df_challenge["rank"] = range(len(df_challenge))  # The pseudo-participant `ground_truth` will get rank=0 and be displayed at the top
        df[f"points_{challenge}"] = n_participants - df_challenge["rank"]  # Participating should give people at least 1 point!

    # Save results as CSV under Leaderboard/
    for challenge in challenges:
        df_challenge = df[df['challenge'] == challenge].sort_values(by="overall_score", ascending=False).drop("challenge", axis="columns")
        df_challenge["rank"] = range(1, len(df_challenge) + 1)
        dfc = df_challenge[["participant", "oc_score", "iou_score", "overall_score", "rank"]].set_index("participant")
        dfc.to_csv(leaderboard_path / f"{challenge}.csv")

    # Update every X sec.
    time.sleep(UPDATE_INTERVAL_SEC)
    
    print("Updating...")