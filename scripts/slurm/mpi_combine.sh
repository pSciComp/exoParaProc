#!/bin/bash
#SBATCH --job-name=exopp_apptainer_mpi
#SBATCH --output=logs/apptainer_%j.out
#SBATCH --error=logs/apptainer_%j.err
#SBATCH --nodes=4                    # Number of compute nodes
#SBATCH --ntasks-per-node=16         # MPI ranks per node (64 total processes)
#SBATCH --cpus-per-task=1            # CPUs allocated per MPI rank
#SBATCH --time=01:00:00              # Wall clock time limit
#SBATCH --partition=compute          # Target cluster partition

# 1. Host Environment Variable Configuration
export HOST_INPUT="/path/to/shared/storage/data/interim"
export HOST_OUTPUT="/path/to/shared/storage/data/final"
export HOST_CONFIG="/path/to/shared/storage/config/mpi_combine.json"

# 2. Container Configuration
# Path to the compiled Apptainer (.sif) image
CONTAINER_IMAGE="/path/to/shared/storage/images/exopp_env.sif"

# Bind mount string: 'host_path:container_path'
# Ensuring the host paths are accessible within the container namespace
BIND_DIRS="${HOST_INPUT}:${HOST_INPUT},${HOST_OUTPUT}:${HOST_OUTPUT},/path/to/shared/storage/config:/path/to/shared/storage/config"

# 3. Environment Initialization
# Load Apptainer and host MPI binaries required for srun
module purge
module load apptainer openmpi

# 4. Hybrid MPI Execution
# srun spawns the MPI ranks on the host network fabric
# apptainer exec maps those ranks to the containerized Python environment
srun apptainer exec \
    --bind ${BIND_DIRS} \
    --env INPUT_PATH=${HOST_INPUT} \
    --env OUTPUT_PATH=${HOST_OUTPUT} \
    --env CONFIG_JSON=${HOST_CONFIG} \
    ${CONTAINER_IMAGE} \
    python scripts/run_mpi_combine.py
