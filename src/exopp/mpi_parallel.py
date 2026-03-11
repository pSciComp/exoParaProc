from collections.abc import Callable
from mpi4py import MPI


def mpi_orchestrator(initiator: Callable,
                     job: Callable,
                     aggregator_cf: Callable,
                     aggregator_processor: Callable,
                     initiator_kwargs: dict | None = None,
                     aggregator_cf_kwargs: dict | None = None) -> None:
    """
    Orchestrates distributed execution utilizing an MPI dedicated I/O rank.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 2:
        raise RuntimeError("MPI execution requires at least 2 ranks (1 I/O, >=1 Compute).")

    initiator_kwargs = initiator_kwargs or {}
    aggregator_cf_kwargs = aggregator_cf_kwargs or {}

    # 1. Job Generation and Distribution (Rank 0)
    if rank == 0:
        all_jobs = initiator(**initiator_kwargs)

        compute_ranks = size - 1
        partitioned_jobs = [
            all_jobs[i::compute_ranks] for i in range(compute_ranks)
        ]
    else:
        partitioned_jobs = None

    # 2. Scatter Jobs
    scatter_payload = [None] + partitioned_jobs if rank == 0 else None
    local_jobs = comm.scatter(scatter_payload, root=0)

    # 3. Execution Splitting
    if rank == 0:
        # --- ORCHESTRATOR / WRITER (Rank 0) ---
        active_workers = size - 1

        # Injection of the agnostic context factory
        with aggregator_cf(**aggregator_cf_kwargs)() as context:
            while active_workers > 0:
                payload = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)

                if payload is None:
                    active_workers -= 1
                    continue

                # Delegation to the injected processor
                aggregator_processor(context, payload)
    else:
        # --- COMPUTE WORKERS (Ranks > 0) ---
        for job_kwargs in local_jobs:
            output_payload = job(**job_kwargs)
            comm.send(output_payload, dest=0, tag=1)

        # Transmission of the termination sentinel
        comm.send(None, dest=0, tag=1)
