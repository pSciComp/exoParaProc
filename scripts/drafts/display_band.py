import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def normalize_array(data_16bit, p2, p98, gamma=0.6):
    """
    Applies a dynamic range stretch and gamma correction using fixed bounds.
    """
    # Convert to float for mathematical operations
    data_float = data_16bit.astype(float)
    # Linear stretch and clipping
    norm = (data_float - p2) / (p98 - p2)
    norm = np.clip(norm, 0.0, 1.0)
    # Non-linear gamma correction and scaling to uint8
    data_8bit = (np.power(norm, gamma) * 255).astype(np.uint8)
    # Mask pure zeros (NoData) from the original array
    data_8bit[data_16bit == 0] = 0
    return data_8bit


def normalize_array_gamma(array, gamma=0.6):
    """
    Applies a 2-98 percentile stretch, scales to [0, 1],
    and applies a non-linear gamma correction.
    """
    array = array.astype(float)
    # Mask pure zero values as NaN
    array[array == 0] = np.nan
    # Calculate statistical bounds
    vmin = np.nanpercentile(array, 2)
    vmax = np.nanpercentile(array, 98)
    # 1. Linear stretch to [0.0, 1.0]
    normalized = np.clip((array - vmin) / (vmax - vmin), 0, 1)
    normalized = np.nan_to_num(normalized, nan=0.0)
    # 2. Non-linear Gamma Correction
    if gamma != 1.0:
        normalized = np.power(normalized, gamma)
    return normalized


# 1. Read and normalize individual bands
bands_data = {}
extents = {}
for color in ["blue", "green", "red"]:
    # with open(f"aletsch_{color}_params.json", 'r') as f:
    #     params = json.load(f)
    #     p2_global = params["p2"]
    #     p98_global = params["p98"]
    # For simplicity
    p2 = 200
    p98 = 9800

    with rasterio.open(f"aletsch_{color}.tif") as src:
        bands_data[color] = normalize_array(src.read(1), p2, p98, gamma=0.6)
        # bands_data[color] = normalize_array_gamma(src.read(1))
        extents[color] = [src.bounds.left,
                          src.bounds.right,
                          src.bounds.bottom,
                          src.bounds.top]


# 2. Generate zero-matrix for non-active channels
z = np.zeros_like(bands_data["red"])

# 3. Construct (H, W, 3) isolated color arrays
blue_isolated = np.dstack((z, z, bands_data["blue"]))
green_isolated = np.dstack((z, bands_data["green"], z))
red_isolated = np.dstack((bands_data["red"], z, z))

# 4. Construct Full True Color Composite
rgb_composite = np.dstack((bands_data["red"],
                           bands_data["green"],
                           bands_data["blue"]))

# 5. Figure and GridSpec Initialization
fig = plt.figure(figsize=(15, 10))
gs = GridSpec(2, 3, figure=fig, height_ratios=[1, 2.5])

ax_blue = fig.add_subplot(gs[0, 0])
ax_green = fig.add_subplot(gs[0, 1])
ax_red = fig.add_subplot(gs[0, 2])
ax_rgb = fig.add_subplot(gs[1, :])

# 6. Render Isolated Color Channels (Row 1)
# No cmap is passed; imshow automatically interprets (H, W, 3) arrays as RGB
ax_blue.imshow(blue_isolated, extent=extents['blue'])
ax_blue.set_title("Blue Band (B02)")

ax_green.imshow(green_isolated, extent=extents['green'])
ax_green.set_title("Green Band (B03)")

ax_red.imshow(red_isolated, extent=extents['red'])
ax_red.set_title("Red Band (B04)")

# 7. Render RGB Composite (Row 2)
ax_rgb.imshow(rgb_composite, extent=extents['red'])
ax_rgb.set_title("True Color Composite (RGB)")
ax_rgb.set_xlabel("Easting (meters)")
ax_rgb.set_ylabel("Northing (meters)")

# 8. Formatting and Export
for ax in [ax_blue, ax_green, ax_red]:
    ax.tick_params(axis='both', which='both',
                   bottom=False, left=False,
                   labelbottom=False, labelleft=False)

output_pdf = "data/final/aletsch_multispectral_isolated.png"
plt.tight_layout()
plt.savefig(output_pdf, format='pdf', dpi=300)
