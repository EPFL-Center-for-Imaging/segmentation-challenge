import marimo

__generated_with = "0.23.8"
app = marimo.App()

with app.setup:
    import io
    import sys
    import os
    import zipfile
    import requests
    from pathlib import Path

    import marimo as mo

    import numpy as np
    import skimage.io


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


    public_folder_path = Path("./public")
    images_path = public_folder_path / "Images"
    ground_truths_path = public_folder_path / "Ground_Truths"

    if "pyodide" in sys.modules:
        # Create the `public` folder
        if not public_folder_path.exists():
            os.mkdir(public_folder_path)

            # Download and unzip the data from the repository
            zip_path = Path("public") / "data.zip"
            url = mo.notebook_location() / "public" / "data.zip"
            r = requests.get(str(url))
            r.raise_for_status()
            zip_path.write_bytes(r.content)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(public_folder_path)
            zip_path.unlink(missing_ok=True)  # Delete the zipped dataset

            print(f"Extracted data in: {public_folder_path}")

    challenges = [d.name for d in ground_truths_path.iterdir() if d.is_dir()]

    # Read all ground truth masks
    ground_truths = {}
    for _challenge in challenges:
        _gt_challenge_folder = ground_truths_path / _challenge
        for gt_file in _gt_challenge_folder.glob("*.tif"):
            _gt_mask = skimage.io.imread(gt_file)
            break  # There should only be one ground truth
        ground_truths[_challenge] = _gt_mask


@app.cell(hide_code=True)
def _(challenges_dropdown):
    image = skimage.io.imread(images_path / f"{challenges_dropdown.value}.tif")
    return


@app.cell(hide_code=True)
def _(challenges_dropdown):
    gt_mask = skimage.io.imread(ground_truths_path / challenges_dropdown.value / f"{challenges_dropdown.value}-gt.tif")
    return (gt_mask,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ![logo](https://imaging.epfl.ch/resources/logo-for-gitlab.svg)
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.hstack(
        [
            mo.md("# Segmentation Challenge"), 
            mo.md("[➡️ GitHub repository](https://github.com/EPFL-Center-for-Imaging/segmentation-challenge)")
        ]
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    Evaluate your submissions. Your submitted files should be

    - in TIFF format
    - a labeled array with values representing instances
    - it should have the same size (same number of pixels in X and Y) than the original image
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Evaluation

    The quality of your submissions is evaluated based on two metrics:

    - **Object count** relative to the ground truth count (`oc_score`).
    - **Intersection over union (IoU)** computed on the binary version of the mask (`iou_score`).

    We also average both scores to give an overall score (`overall_score`).
    """)
    return


@app.cell(hide_code=True)
def _():
    challenges_dropdown = mo.ui.dropdown(challenges, value=challenges[0], label="Challenge")

    challenges_dropdown
    return (challenges_dropdown,)


@app.cell
def _():
    file_drop = mo.ui.file(filetypes=[".tif"], kind="area", label="Drag and drop your submission file here (.tif)")

    file_drop
    return (file_drop,)


@app.cell
def _(file_drop):
    if file_drop.contents():
        # TODO: add a little spinner
        mask = skimage.io.imread(io.BytesIO(file_drop.contents()))
    else:
        mask = None
    return (mask,)


@app.cell
def _(gt_mask, mask):
    mo.stop(not isinstance(mask, np.ndarray), mo.callout("Upload a mask file to evaluate it against the ground truth.", kind="info"))

    valid_mask = gt_mask.shape == mask.shape
    return (valid_mask,)


@app.cell
def _(challenges_dropdown, gt_mask, mask, valid_mask):
    mo.stop(not valid_mask, mo.callout(f"The uploaded mask file is invalid for the selected challenge ({challenges_dropdown.value}).", kind="danger"))

    oc_score = object_count_score(gt_mask, mask)

    iou_score = binary_iou_score(gt_mask, mask)

    overall_score = np.mean([oc_score, iou_score])

    # TODO: make a lovely print:
    mo.vstack([
        oc_score, iou_score, overall_score
    ])
    return


@app.cell
def _():
    # display_nicely(gt_mask, mask, image)
    return


if __name__ == "__main__":
    app.run()
