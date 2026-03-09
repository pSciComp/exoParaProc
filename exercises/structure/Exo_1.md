# Structure E1: Parallelization Workflow

> [!WARNING]
> _⏳ Exercise will be ready by March 13, 2026 ⏳_


In a first step we focus on intra-node parallelization written purely in Python.
['multiprocessing'](https://docs.python.org/3/library/multiprocessing.html) is Pythons go to library for such implementation of parallelization.

The `multiplrocessing` library might take some getting used to.
But if you have a clear mental picture of the rough architecture of a parallelization (and more generally any concurrency implementation) workflow, the `multiprocessing` package becomes much easier to digest.

## Your Tasks:

- Recall the Concurrency workflow from [the introduction to Concurrency](https://psicomp.courses.t4d.ch/content/utilizingSharedResources/soruce/content/concurrency/index.html#concurrency-workflow) with the 4 elements:
  1. **Orchestration**
  1. **Initiation**
  1. **Job(s)**
  1. **Aggregation**

  Checkout the codebase of the project (i.e. under `src/exopp`) and try to identify the functions that would each map to these architectural elements.
