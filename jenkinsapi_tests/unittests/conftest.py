"""Pytest configuration for unit tests."""

import pytest


@pytest.fixture(scope="session")
def num_workers(request):
    if hasattr(request.config, "workerinput"):
        num_workers = request.config.workerinput.get("workerinput", {}).get(
            "num_workers", 1
        )
    else:
        worker_arg = request.config.option.dist
        if (
            worker_arg
            and worker_arg.startswith("load")
            or worker_arg == "each"
        ):
            num_workers = getattr(
                request.config,
                "_xdist_worker_count",
                request.config.getoption("-n", 1),
            )
        else:
            num_workers = 1

    return int(num_workers) if num_workers and num_workers != "no" else 1
