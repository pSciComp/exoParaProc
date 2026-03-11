import warnings
from typing import Any, Optional, ContextManager
from collections.abc import Callable, Collection
import multiprocessing as mpc

MPC_STARTER_METHODS = ['spawn', 'fork', 'forkserver']


def get_or_set_context(method: Optional[str] = None) -> mpc.context.BaseContext:
    allowed = MPC_STARTER_METHODS + [None, ]
    default_method = MPC_STARTER_METHODS[0]
    if method not in allowed:
        raise ValueError(f"Unsupported start method: {method!r}")

    _context = mpc.get_start_method(allow_none=True)

    if _context is None:
        if method is not None:
            try:
                mpc.set_start_method(method)
            except RuntimeError:
                warnings.warn(
                    "Race when setting start method; returning requested context.",
                    RuntimeWarning)
            finally:
                _context = method
        else:
            warnings.warn(
                "No multiprocessing start method set and no global either"
                f"— defaulting to local context only with '{default_method}'.",
                RuntimeWarning
            )
            _context = default_method
    else:
        if method is not None:
            if method != _context:
                warnings.warn(
                    f"Global multiprocessing start method is '{_context}'"
                    f" but requested context is '{method}'"
                    f"— using local context only with '{method}'"
                    "keeping the global unchanged.",
                    RuntimeWarning
                )
                _context = method
    return mpc.get_context(_context)


def get_nbr_workers(number: Optional[int] = None) -> int:
    _min_count = 2
    if number is None:
        _use = max(_min_count, mpc.cpu_count())
    elif number <= _min_count:
        warnings.warn(
            message=f"For this routine to work properly at least {_min_count} "
                    f"workers are required - the requested {number} are not "
                    "enough and thus the request will be ignored.",
            category=RuntimeWarning
        )
        _use = _min_count
    else:
        _use = int(number)
    return _use


def job_call(out_queue: mpc.Queue,
             callback: Callable,
             kwargs: dict,
             wrapper: Callable | None = None) -> dict:
    """Put the results of callback using parameter into the queue"""
    output = callback(**kwargs)
    if wrapper is not None:
        out_queue.put(wrapper(output))
    else:
        out_queue.put(output)
    return output


def aggregator(
    queue: mpc.Queue,
    context_factory: Callable[[], ContextManager[Any]],
    process_payload: Callable[[Any, Any], None]
) -> None:
    with context_factory() as context:
        while True:
            payload = queue.get()
            if payload is None:
                break
            process_payload(context, payload)


def orchestrator(initiator: Callable,
                 job: Callable,
                 aggregator_func: Callable,
                 aggregator_cf: Callable,
                 aggregator_processor: Callable,
                 aggregator_cf_kwargs: dict | None = None,
                 initiator_kwargs: dict | None = None,
                 nbrcpu: int | None = None,
                 start_method: str | None = None,
                 ):
    initiator_kwargs = initiator_kwargs or {}
    jobs_params = initiator(**initiator_kwargs)

    manager = mpc.Manager()
    aggregation_q = manager.Queue()

    aggregator_cf_kwargs = aggregator_cf_kwargs or dict()
    aggregator_proc = mpc.Process(
        target=aggregator_func,
        kwargs=dict(queue=aggregation_q,
                    context_factory=aggregator_cf(**aggregator_cf_kwargs),
                    process_payload=aggregator_processor)
    )
    aggregator_proc.start()

    nbr_workers = get_nbr_workers(number=nbrcpu) - 1

    with get_or_set_context(start_method).Pool(nbr_workers) as pool:
        all_jobs = []
        for job_params in jobs_params:
            all_jobs.append(pool.apply_async(
                func=job_call,
                kwds=dict(out_queue=aggregation_q,
                          callback=job,
                          kwargs=job_params)
            ))

        job_outputs = []
        for job_async_call in all_jobs:
            job_outputs.append(job_async_call.get())

        pool.close()
        pool.join()

    aggregation_q.put(None)
    aggregator_proc.join()
