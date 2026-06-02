# Segmenting `sunflowers.tif` in Fiji

Here is a simple workflow in [Fiji](https://fiji.sc/) to segment the sunflower seeds:

- Open `sunflowers.tif` in Fiji.
- `Image` => `Type` => `8-bit` to convert the image to grayscale.
- `Image` => `Adjust` => `Threshold..` to open the intensity threshold menu.
- Set the automatic threshold to `Otsu` and tick `Dark background`. Then, click `Apply` to binarize the image.
- `Analyze` => `Analyze Particles..` to open the particle analysis menu.
- Under `Size`, select `300-5000` to include only that particle size range.
- Under `Show`, select `Count Masks` to output a labelled array. Then, click `OK`.
- This should produce a labelled segmentation mask of the sunflower seeds! You can save it via `File` > `Save As` => `Tiff`.