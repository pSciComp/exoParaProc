# Parallel Processing Exercise

This python project focuses on the implementation of parallelisation.

Conceptually, when concerned with parallelisms, or other forms of concurrent processing, we must consider 4 parts:

1. Orchestration: An overarching process that managed the tree other parts.
2. Separation: The process that prepares input and configuration for the individual steps jobs.
3. Jobs: These are the processes that will run in parallel (or, more generally, concurrently).
4. Aggregation: The process that digests and potentially combines the outcome of the individual jobs.

On a single multi-core CPU we might handle the 4 parts in a compact manner, e.g. using pythons [multiprocessing](url) library, on more elaborated compute infrastructures, like an HPC slurm cluster, we might implement the orchestration in a bash script and have individual jobs run on completely distinct machines.

## Usage

This project contains various exercises defined under [./exercises](./exercises).
To get started head over to [Exercise 0](./exercises/Exo_0.md) that will guide you through the initial setup.
