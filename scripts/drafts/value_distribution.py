import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Configuration parameters
input_tif = "aletsch_red.tif"
output_pdf = "histogram_transformation.pdf"
gamma_value = 0.6

# 1. Accumulate 16-bit histogram via memory-efficient windowed reading
hist_16bit = np.zeros(65536, dtype=np.int64)

with rasterio.open(input_tif) as src:
    nodata = src.nodata if src.nodata is not None else 0
    
    for _, window in src.block_windows(1):
        data = src.read(1, window=window)
        # Exclude NoData pixels to prevent statistical skew
        valid_data = data[data != nodata]
        
        # Accumulate frequencies; ensure length constraint
        counts = np.bincount(valid_data.ravel(), minlength=65536)
        hist_16bit += counts[:65536]

# 2. Compute Cumulative Distribution Function (CDF) and Extract Percentiles
total_valid = np.sum(hist_16bit)
if total_valid == 0:
    raise ValueError("No valid data pixels found in the raster.")

cdf = np.cumsum(hist_16bit) / total_valid

p2 = np.argmax(cdf >= 0.02)
p98 = np.argmax(cdf >= 0.98)

print(f"Calculated 2nd Percentile: {p2}")
print(f"Calculated 98th Percentile: {p98}")

# 3. Construct 16-bit to 8-bit Look-Up Table (LUT)
bins_16bit = np.arange(65536, dtype=float)

# Apply linear stretch and mathematical clipping
norm = (bins_16bit - p2) / (p98 - p2)
norm = np.clip(norm, 0.0, 1.0)

# Apply non-linear gamma correction and scale to uint8 range
lut_8bit = (np.power(norm, gamma_value) * 255).astype(np.uint8)

# 4. Redistribute Histogram Counts using LUT
hist_8bit = np.zeros(256, dtype=np.int64)
np.add.at(hist_8bit, lut_8bit, hist_16bit)

# 5. Figure Generation and Formatting
p99 = np.argmax(cdf >= 0.99) # Upper bound for clear visualization

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Subplot 1: Original 16-bit Distribution
axes[0].plot(np.arange(p99), hist_16bit[:p99], color='black')
axes[0].fill_between(np.arange(p99), hist_16bit[:p99], color='gray', alpha=0.5)
axes[0].axvline(p2, color='red', linestyle='--', label=f'2nd Pct ({p2})')
axes[0].axvline(p98, color='blue', linestyle='--', label=f'98th Pct ({p98})')
axes[0].set_title("Original Distribution (uint16)")
axes[0].set_xlabel("Surface Reflectance")
axes[0].set_ylabel("Pixel Count")
axes[0].legend()

# Subplot 2: Transformed 8-bit Distribution
# Bins 0 and 255 are excluded from the plot boundaries to highlight internal variance
axes[1].plot(np.arange(1, 255), hist_8bit[1:255], color='green')
axes[1].fill_between(np.arange(1, 255), hist_8bit[1:255], color='lightgreen', alpha=0.5)
axes[1].set_title(f"Gamma Corrected Distribution (uint8, $\gamma={gamma_value}$)")
axes[1].set_xlabel("Pixel Value (1-254)")
axes[1].set_ylabel("Pixel Count")

plt.tight_layout()
plt.savefig(output_pdf, format='pdf', dpi=300)
print(f"Transformation histogram exported to {output_pdf}")
