import marimo

__generated_with = "0.23.8"
app = marimo.App(width="full")

async with app.setup:
    import io
    import sys
    import os
    import zipfile
    import requests
    import copy
    from pathlib import Path

    import marimo as mo

    import numpy as np
    import skimage.io
    from skimage.measure import find_contours
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots


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


    def scatters_from_mask(mask):
        _labs = np.unique(mask)
        _labs = _labs[_labs != 0]
        _n_labs = len(_labs)
    
        _rng = np.random.default_rng(42)
        _colors = {i: f"rgb({r},{g},{b})" for i, (r,g,b) in zip(_labs, _rng.integers(0, 255, (_n_labs, 3)))}
    
        _mask_scatters = []
    
        for _lab in _labs:
            for _contour in find_contours(mask == _lab, 0.5):
                _mask_scatters.append(
                    go.Scatter(
                        x=_contour[:, 1],
                        y=_contour[:, 0],
                        mode="lines",
                        line=dict(color=_colors[int(_lab)], width=2),
                        showlegend=False,
                    )
                )

        return _mask_scatters


    public_folder_path = Path("./public")
    images_path = public_folder_path / "Images"
    ground_truths_path = public_folder_path / "Ground_Truths"

    if "pyodide" in sys.modules:
        import micropip
        await micropip.install("tifffile==2025.5.10")

        if not public_folder_path.exists():
            # Download and unzip the public folder from the repository
            zip_path = Path("public.zip")
            url = "https://raw.githubusercontent.com/EPFL-Center-for-Imaging/segmentation-challenge/main/public.zip"
            r = requests.get(str(url))
            r.raise_for_status()
            zip_path.write_bytes(r.content)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall()

            print(f"Extracted data in: {public_folder_path}")

    challenges = [d.name for d in ground_truths_path.iterdir() if d.is_dir()]

    # Read all ground truth masks
    ground_truths = {}
    for _challenge in challenges:
        _gt_challenge_folder = ground_truths_path / _challenge
        for gt_file in _gt_challenge_folder.glob("*.tif"):
            _gt_mask = skimage.io.imread(gt_file)
            break  # There should only be one ground truth
        _gt_scatter = scatters_from_mask(_gt_mask)
        ground_truths[_challenge] = (_gt_mask, _gt_scatter)


@app.cell(hide_code=True)
def _(challenges_dropdown):
    image = skimage.io.imread(images_path / f"{challenges_dropdown.value}.tif")
    return (image,)


@app.cell(hide_code=True)
def _(challenges_dropdown):
    gt_mask, gt_scatter = ground_truths[challenges_dropdown.value] #skimage.io.imread(ground_truths_path / challenges_dropdown.value / f"{challenges_dropdown.value}-gt.tif")
    return gt_mask, gt_scatter


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
    challenges_dropdown = mo.ui.dropdown(challenges, value=challenges[0], label="Challenge")

    mo.callout(mo.hstack([challenges_dropdown], justify="center"), kind="neutral")
    return (challenges_dropdown,)


@app.cell
def _():
    file_drop = mo.ui.file(filetypes=[".tif"], kind="area", label="Drag and drop your submission file here (.tif)")

    file_drop
    return (file_drop,)


@app.cell
def _(file_drop):
    if file_drop.contents():
        with mo.status.spinner(title=f"Loading mask...") as _spinner:
            mask = skimage.io.imread(io.BytesIO(file_drop.contents()))
            mask_scatters = scatters_from_mask(mask)
    else:
        mask = None
    return mask, mask_scatters


@app.cell
def _(gt_mask, mask):
    mo.stop(not isinstance(mask, np.ndarray), mo.callout("Upload a mask file to evaluate it against the ground truth.", kind="info"))

    valid_mask = gt_mask.shape == mask.shape
    return (valid_mask,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Evaluation

    The quality of your submissions is evaluated based on two metrics:

    - **Object count** relative to the ground truth count.
    - **Intersection over union (IoU)** computed on the binary version of the mask.

    We also average both scores to give an overall score.
    """)
    return


@app.cell
def _(challenges_dropdown, gt_mask, mask, valid_mask):
    mo.stop(not valid_mask, mo.callout(f"The uploaded mask file is invalid for the selected challenge ({challenges_dropdown.value}).", kind="danger"))

    oc_score = object_count_score(gt_mask, mask)

    iou_score = binary_iou_score(gt_mask, mask)

    overall_score = np.mean([oc_score, iou_score])

    mo.vstack([
            mo.md("Your Submission Scores"),
            mo.hstack([mo.md(
                f"""| Object count | IoU | Average |
                | ------ | ------ | ------ |
                | {oc_score*100:.0f} % | {iou_score*100:.0f} % | {overall_score*100:.0f} % |
                """
            )]),
        ], align="center",
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    Here is a comparison between the ground truth mask and your submission:
    """)
    return


@app.cell
def _(gt_scatter, image, mask):
    viewer_size = 500

    base = px.imshow(
        image,
        height=viewer_size,
        color_continuous_scale="gray",
        contrast_rescaling="minmax",
        aspect="equal",
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.5, 0.5],
        horizontal_spacing=0.02,
        subplot_titles=("Ground truth", "Submission"),
    )

    fig.update_annotations(
        font=dict(size=16, color="white")
    )

    for tr in base.data:
        fig.add_trace(copy.deepcopy(tr), row=1, col=1)

    for tr in gt_scatter:
        fig.add_trace(copy.deepcopy(tr), row=1, col=1)

    for ax in ["xaxis", "xaxis2"]:
        fig.layout[ax].update(
            showticklabels=False,
            showgrid=False,
            visible=False,
            zeroline=False,
        )

    for ax, xanchor in [("yaxis", "x"), ("yaxis2", "x2")]:
        fig.layout[ax].update(
            showticklabels=False,
            showgrid=False,
            visible=False,
            zeroline=False,
            scaleanchor=xanchor,
            autorange="reversed",
        )

    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, b=30, t=30, pad=0),
        plot_bgcolor="black",
        paper_bgcolor="black",
        showlegend=False,
    )

    mo.ui.plotly(fig) if not isinstance(mask, np.ndarray) else None
    return (viewer_size,)


@app.cell
def _(gt_scatter, image, mask_scatters, valid_mask, viewer_size):
    mo.stop(not valid_mask)


    base2 = px.imshow(
        image,
        height=viewer_size,
        color_continuous_scale="gray",
        contrast_rescaling="minmax",
        aspect="equal",
    )

    fig2 = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.5, 0.5],
        horizontal_spacing=0.02,
        subplot_titles=("Ground truth", "Submission"),
    )

    fig2.update_annotations(
        font=dict(size=16, color="white")
    )

    for _tr in base2.data:
        fig2.add_trace(copy.deepcopy(_tr), row=1, col=1)

    for _tr in gt_scatter:
        fig2.add_trace(copy.deepcopy(_tr), row=1, col=1)


    # Added this:
    for _tr in base2.data:
        fig2.add_trace(copy.deepcopy(_tr), row=1, col=2)

    for _tr in mask_scatters:
        fig2.add_trace(copy.deepcopy(_tr), row=1, col=2)
    # ----------

    for _ax in ["xaxis", "xaxis2"]:
        fig2.layout[_ax].update(
            showticklabels=False,
            showgrid=False,
            visible=False,
            zeroline=False,
        )

    for _ax, _xanchor in [("yaxis", "x"), ("yaxis2", "x2")]:
        fig2.layout[_ax].update(
            showticklabels=False,
            showgrid=False,
            visible=False,
            zeroline=False,
            scaleanchor=_xanchor,
            autorange="reversed",
        )

    fig2.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, b=30, t=30, pad=0),
        plot_bgcolor="black",
        paper_bgcolor="black",
        showlegend=False,
    )

    mo.ui.plotly(fig2)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
