"""
Pytest configuration for unit tests.

Handles xdist worker coordination and resource constraints.
"""

import pytest


@pytest.fixture(scope="session")
def num_workers(request):
    """
    Detect number of xdist workers and make available to fixtures.

    Returns:
        int: Number of workers (1 if no xdist, or actual worker count)
    """
    if hasattr(request.config, "workerinput"):
        # Running with xdist - get total number of workers
        num_workers = request.config.workerinput.get("workerinput", {}).get(
            "num_workers", 1
        )
    else:
        # Check if xdist is being used via command line option
        worker_arg = request.config.option.dist
        if (
            worker_arg
            and worker_arg.startswith("load")
            or worker_arg == "each"
        ):
            # xdist is active, try to get worker count from session
            num_workers = getattr(
                request.config,
                "_xdist_worker_count",
                request.config.getoption("-n", 1),
            )
        else:
            num_workers = 1

    return int(num_workers) if num_workers and num_workers != "no" else 1
