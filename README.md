# Parallel Processing Exercise

This project focuses on the implementation of parallel processing architectures in Python.

The objective is the generation of a high-resolution (10m x 10m) True Color (RGB) composite satellite image covering central Switzerland.
This composite is derived from MultiSpectral Instrument (MSI) data acquired by the European Space Agency's (ESA) Sentinel-2 satellite constellation.

The MSI sensor provides high-resolution surface reflectance measurements across three narrow visible wavelength bands: Blue (~490 nm), Green (~560 nm), and Red (~665 nm).
Data is encoded as 16-bit unsigned integers (`uint16`), offering a dynamic range of 0 to 65,535.

The physical unit is Bottom-of-Atmosphere (BOA) surface reflectance, where a value of 10,000 corresponds to 100% reflectance (Main-Knorn et al., 2017). 
Although values exceeding 10,000 are physically possible due to anisotropic scattering and specular reflection, an absolute upper bound of 10,000 is defined for this implementation.
To translate these linear reflectance intensities into human-interpretable RGB color spaces and ensure radiometric consistency across independent spatial chunks, the data is clamped at 10,000, normalized, and a non-linear gamma correction is applied to map the reflectance intensities to an 8-bit (0-255) RGB color space (Richards & Jia, 2006).

Consequently, the three discrete spectral arrays must be radiometrically scaled and spatially stacked in order to create a visual image:

[!Illustration](./data/final/aletsch_multispectral_isolated.png)

## Computational Bottleneck and Parallelization

The processing of three high-resolution two-dimensional arrays spanning a regional extent requires significant system memory (RAM).
A continuous in-memory computation, including Python-specific object overhead and 64-bit floating-point transformations, is estimated to demand approximately 5 GB of RAM.
This computational footprint is mitigated through parallelization.

The radiometric transformation is an embarrassingly parallel problem.
Spatial chunking is facilitated by the Geospatial Data Abstraction Library (GDAL), an open-source C/C++ translator library for raster data (GDAL/OGR contributors, 2024).
GDAL enables windowed read operations, allowing the primary task to be partitioned into discrete, independent jobs that operate on small spatial subsets.

However, standard GDAL bindings do not support concurrent, lock-free write operations to a single `.tif` file from multiple isolated processes.
Uncoordinated parallel writes yield file corruption.
To resolve this concurrency limitation, a Queue-Writer architecture can be implemented.
Each independent job reads the reflectance data for its assigned spatial window, applies the mathematical transformations, and prepares an isolated 3D array (Height $\times$ Width $\times$ 3) holding the computed RGB values.
These arrays are subsequently pushed to a multiprocessing queue.
A dedicated aggregation task sequentially retrieves these arrays from the queue and executes the write operations to the final full-resolution image.


## Architecture of Concurrent Processing

The conceptual architecture of this concurrent processing pipeline necessitates four distinct components:

1. **Orchestration:** A supervisory process responsible for the execution and lifecycle management of the subsequent components.
2. **Separation/Initiation:** The mechanism that partitions the input data into discrete spatial windows and generates the specific configurations for isolated execution.
3. **Jobs:** The independent computational units executed concurrently (e.g., windowed data extraction, transformation, and 3D RGB array generation).
4. **Aggregation:** The dedicated writer process that sequentially digests the 3D arrays from a multiprocessing queue and constructs the final output file without locking conflicts.

On a single multi-core workstation, these components can be managed via Python's standard `multiprocessing` library.
In distributed compute environments, such as a High-Performance Computing (HPC) cluster managed by Slurm, orchestration is often shifted to shell scripts, with independent jobs dispatched across distinct physical nodes.

**References:**

* GDAL/OGR contributors (2024). *GDAL/OGR Geospatial Data Abstraction software Library*. Open Source Geospatial Foundation. URL: [https://gdal.org](https://gdal.org)
* Main-Knorn, M., et al. (2017). Sen2Cor for Sentinel-2. *Image and Signal Processing for Remote Sensing XXIII*, 10427. SPIE.
* Richards, J. A., & Jia, X. (2006). *Remote Sensing Digital Image Analysis: An Introduction* (4th ed.). Springer.

---

## Usage

This project contains various exercises defined under [./exercises](./exercises).
To get started head over to [Exercise 0](./exercises/Exo_0.md) that will guide you through the initial setup.

